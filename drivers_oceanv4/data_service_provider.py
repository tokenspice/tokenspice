#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import json
import logging
import os
import re
from collections import namedtuple
from decimal import Decimal
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import requests
from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from drivers_oceanv4.service_types import ServiceTypes
from drivers_oceanv4.requests_session import get_requests_session
from drivers_oceanv4.config import Config
from drivers_oceanv4.exceptions import OceanEncryptAssetUrlsError
from drivers_oceanv4.algorithm_metadata import AlgorithmMetadata
from drivers_oceanv4.env_constants import ENV_PROVIDER_API_VERSION
from drivers_oceanv4.currency import to_wei
from drivers_oceanv4.transactions import sign_hash
from drivers_oceanv4.wallet import Wallet
from requests.exceptions import InvalidURL
from requests.models import PreparedRequest, Response
from requests.sessions import Session

logger = logging.getLogger(__name__)

OrderRequirements = namedtuple(
    "OrderRequirements",
    ("amount", "data_token_address", "receiver_address", "nonce", "computeAddress"),
)


class DataServiceProvider:
    """DataServiceProvider class.

    The main functions available are:
    - consume_service
    - run_compute_service (not implemented yet)
    """

    _http_client = get_requests_session()
    API_VERSION = "/api/v1"
    provider_info = None

    @staticmethod
    @enforce_types
    def get_http_client() -> Session:
        """Get the http client."""
        return DataServiceProvider._http_client

    @staticmethod
    @enforce_types
    def set_http_client(http_client: Session) -> None:
        """Set the http client to something other than the default `requests`."""
        DataServiceProvider._http_client = http_client

    @staticmethod
    @enforce_types
    def encrypt_files_dict(
        files_dict: list,
        encrypt_endpoint: str,
        asset_id: str,
        publisher_address: str,
        signed_did: str,
    ) -> str:
        payload = json.dumps(
            {
                "documentId": asset_id,
                "signature": signed_did,
                "document": json.dumps(files_dict),
                "publisherAddress": publisher_address,
            }
        )

        response = DataServiceProvider._http_method(
            "post",
            encrypt_endpoint,
            data=payload,
            headers={"content-type": "application/json"},
        )
        if response and hasattr(response, "status_code"):
            if response.status_code != 201:
                msg = (
                    f"Encrypt file urls failed at the encryptEndpoint "
                    f"{encrypt_endpoint}, reason {response.text}, status {response.status_code}"
                )
                logger.error(msg)
                raise OceanEncryptAssetUrlsError(msg)

            logger.info(
                f"Asset urls encrypted successfully, encrypted urls str: {response.text},"
                f" encryptedEndpoint {encrypt_endpoint}"
            )

            return response.json()["encryptedDocument"]

        return ""

    @staticmethod
    @enforce_types
    def sign_message(
        wallet: Wallet,
        msg: str,
        nonce: Optional[Union[str, int]] = None,
        provider_uri: Optional[str] = None,
    ) -> str:
        if nonce is None:
            nonce = str(DataServiceProvider.get_nonce(wallet.address, provider_uri))
        print(f"signing message with nonce {nonce}: {msg}, account={wallet.address}")
        return sign_hash(encode_defunct(text=f"{msg}{nonce}"), wallet)

    @staticmethod
    @enforce_types
    def get_nonce(user_address: str, provider_uri: str) -> Optional[Union[str, int]]:
        _, url = DataServiceProvider.build_endpoint("nonce", provider_uri=provider_uri)
        response = DataServiceProvider._http_method(
            "get", f"{url}?userAddress={user_address}"
        )
        if response.status_code != 200:
            return None

        return response.json()["nonce"]

    @staticmethod
    @enforce_types
    def get_order_requirements(
        did: str,
        service_endpoint: str,
        consumer_address: str,
        service_id: Union[str, int],
        service_type: str,
        token_address: str,
        userdata: Optional[Dict] = None,
    ) -> Optional[OrderRequirements]:
        """

        :param did:
        :param service_endpoint:
        :param consumer_address: hex str the ethereum account address of the consumer
        :param service_id:
        :param service_type:
        :param token_address:
        :return: OrderRequirements instance -- named tuple (amount, data_token_address, receiver_address, nonce),

        """

        req = PreparedRequest()
        params = {
            "documentId": did,
            "serviceId": service_id,
            "serviceType": service_type,
            "dataToken": token_address,
            "consumerAddress": consumer_address,
        }

        if userdata:
            userdata = json.dumps(userdata)
            params["userdata"] = userdata

        req.prepare_url(service_endpoint, params)
        initialize_url = req.url

        logger.info(f"invoke the initialize endpoint with this url: {initialize_url}")
        response = DataServiceProvider._http_method("get", initialize_url)
        # The returned json should contain information about the required number of tokens
        # to consume `service_id`. If service is not available there will be an error or
        # the returned json is empty.
        if response.status_code != 200:
            return None
        order = dict(response.json())

        return OrderRequirements(
            to_wei(
                Decimal(order["numTokens"])
            ),  # comes as float, needs to be converted
            order["dataToken"],
            order["to"],
            int(order["nonce"]),
            order.get("computeAddress"),
        )

    @staticmethod
    @enforce_types
    def download_service(
        did: str,
        service_endpoint: str,
        wallet: Wallet,
        files: List[Dict[str, Any]],
        destination_folder: Union[str, Path],
        service_id: int,
        token_address: str,
        order_tx_id: str,
        index: Optional[int] = None,
        userdata: Optional[Dict] = None,
    ) -> None:
        """
        Call the provider endpoint to get access to the different files that form the asset.

        :param did: str id of the asset
        :param service_endpoint: Url to consume, str
        :param wallet: hex str Wallet instance of the consumer signing this request
        :param files: List containing the files to be consumed, list
        :param destination_folder: Path, str
        :param service_id: integer the id of the service inside the DDO's service dict
        :param token_address: hex str the data token address associated with this asset/service
        :param order_tx_id: hex str the transaction hash for the required data token
            transfer (tokens of the same token address above)
        :param index: Index of the document that is going to be downloaded, int
        :return: True if was downloaded, bool
        """
        indexes = range(len(files))
        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")
            assert index < len(files), logger.error(
                "index can not be bigger than the number of files"
            )
            indexes = [index]

        req = PreparedRequest()
        params = {
            "documentId": did,
            "serviceId": service_id,
            "serviceType": ServiceTypes.ASSET_ACCESS,
            "dataToken": token_address,
            "transferTxId": order_tx_id,
            "consumerAddress": wallet.address,
        }

        if userdata:
            userdata = json.dumps(userdata)
            params["userdata"] = userdata

        req.prepare_url(service_endpoint, params)
        base_url = req.url

        provider_uri = DataServiceProvider.get_root_uri(service_endpoint)
        for i in indexes:
            signature = DataServiceProvider.sign_message(
                wallet, did, provider_uri=provider_uri
            )
            download_url = base_url + f"&signature={signature}&fileIndex={i}"
            logger.info(f"invoke consume endpoint with this url: {download_url}")
            response = DataServiceProvider._http_method(
                "get", download_url, stream=True
            )
            file_name = DataServiceProvider._get_file_name(response)
            DataServiceProvider.write_file(
                response, destination_folder, file_name or f"file-{i}"
            )

    @staticmethod
    @enforce_types
    def start_compute_job(
        did: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
        service_id: int,
        order_tx_id: str,
        algorithm_did: Optional[str] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_tx_id: Optional[str] = None,
        algorithm_data_token: Optional[str] = None,
        output: Optional[dict] = None,
        input_datasets: Optional[list] = None,
        job_id: Optional[str] = None,
        userdata: Optional[dict] = None,
        algouserdata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """

        :param did: id of asset starting with `did:op:` and a hex str without 0x prefix
        :param service_endpoint:
        :param consumer_address: hex str the ethereum address of the consumer executing the compute job
        :param signature: hex str signed message to allow the provider to authorize the consumer
        :param service_id:
        :param order_tx_id: hex str id of the token transfer transaction
        :param algorithm_did: str -- the asset did (of `algorithm` type) which consist of `did:op:` and
            the assetId hex str (without `0x` prefix)
        :param algorithm_meta: see `OceanCompute.execute`
        :param algorithm_tx_id: transaction hash of algorithm StartOrder tx (Required when using `algorithm_did`)
        :param algorithm_data_token: datatoken address of this algorithm (Required when using `algorithm_did`)
        :param output: see `OceanCompute.execute`
        :param input_datasets: list of ComputeInput
        :param job_id: str id of compute job that was started and stopped (optional, use it
            here to start a job after it was stopped)
        :return: job_info dict with jobId, status, and other values
        """
        assert (
            algorithm_did or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        payload = DataServiceProvider._prepare_compute_payload(
            did,
            consumer_address,
            service_id,
            order_tx_id,
            signature=signature,
            algorithm_did=algorithm_did,
            algorithm_meta=algorithm_meta,
            algorithm_tx_id=algorithm_tx_id,
            algorithm_data_token=algorithm_data_token,
            output=output,
            input_datasets=input_datasets,
            job_id=job_id,
            userdata=userdata,
            algouserdata=algouserdata,
        )
        logger.info(f"invoke start compute endpoint with this url: {payload}")
        response = DataServiceProvider._http_method(
            "post",
            service_endpoint,
            data=json.dumps(payload),
            headers={"content-type": "application/json"},
        )
        if response is None:
            raise AssertionError(
                f"Failed to get a response for request: serviceEndpoint={service_endpoint}, payload={payload}, response is {response}"
            )

        logger.debug(
            f"got DataProvider execute response: {response.content} with status-code {response.status_code} "
        )

        logger.debug(
            f"got DataProvider execute response: {response.content} with status-code {response.status_code} "
        )

        if response.status_code not in (201, 200):
            raise ValueError(response.content.decode("utf-8"))

        try:
            job_info = json.loads(response.content.decode("utf-8"))
            if isinstance(job_info, list):
                return job_info[0]
            return job_info

        except KeyError as err:
            logger.error(f"Failed to extract jobId from response: {err}")
            raise KeyError(f"Failed to extract jobId from response: {err}")
        except JSONDecodeError as err:
            logger.error(f"Failed to parse response json: {err}")
            raise

    @staticmethod
    @enforce_types
    def stop_compute_job(
        did: str,
        job_id: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
    ) -> Dict[str, Any]:
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: bool whether the job was stopped successfully
        """
        return DataServiceProvider._send_compute_request(
            "put", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    @enforce_types
    def delete_compute_job(
        did: str,
        job_id: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
    ) -> Dict[str, str]:
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: bool whether the job was deleted successfully
        """
        return DataServiceProvider._send_compute_request(
            "delete", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    @enforce_types
    def compute_job_status(
        did: str,
        job_id: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
    ) -> Dict[str, Any]:
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: dict of job_id to status info. When job_id is not provided, this will return
            status for each job_id that exist for the did
        """
        return DataServiceProvider._send_compute_request(
            "get", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    @enforce_types
    def compute_job_result(
        did: str,
        job_id: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
    ) -> Dict[str, Any]:
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: dict of job_id to result urls. When job_id is not provided, this will return
            result for each job_id that exist for the did
        """
        return DataServiceProvider._send_compute_request(
            "get", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    @enforce_types
    def compute_job_result_file(
        job_id: str,
        index: int,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
    ) -> Dict[str, Any]:
        """

        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param index: int compute result index
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: dict of job_id to result urls.
        """
        req = PreparedRequest()
        params = {
            "signature": signature,
            "jobId": job_id,
            "index": index,
            "consumerAddress": consumer_address,
        }

        req.prepare_url(service_endpoint, params)
        compute_job_result_file_url = req.url

        logger.info(
            f"invoke the computeResult endpoint with this url: {compute_job_result_file_url}"
        )
        response = DataServiceProvider._http_method("get", compute_job_result_file_url)

        if response.status_code != 200:
            raise Exception(response.content)

        return response.content

    @staticmethod
    @enforce_types
    def _remove_slash(path: str) -> str:
        if path.endswith("/"):
            path = path[:-1]
        if path.startswith("/"):
            path = path[1:]
        return path

    @staticmethod
    @enforce_types
    def get_url(config: Config) -> str:
        """
        Return the DataProvider component url.

        :param config: Config
        :return: Url, str
        """
        return DataServiceProvider._remove_slash(config.provider_url)

    @staticmethod
    @enforce_types
    def get_api_version() -> str:
        return DataServiceProvider._remove_slash(
            os.getenv(ENV_PROVIDER_API_VERSION, DataServiceProvider.API_VERSION)
        )

    @staticmethod
    @enforce_types
    def get_service_endpoints(provider_uri: str) -> Dict[str, List[str]]:
        """
        Return the service endpoints from the provider URL.
        """
        provider_info = DataServiceProvider._http_method("get", provider_uri).json()

        return provider_info["serviceEndpoints"]

    @staticmethod
    @enforce_types
    def get_c2d_address(provider_uri: str) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            provider_info = DataServiceProvider._http_method("get", provider_uri).json()

            return provider_info["computeAddress"]
        except requests.exceptions.RequestException:
            pass

        return None

    @staticmethod
    @enforce_types
    def get_provider_address(provider_uri: str) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            provider_info = DataServiceProvider._http_method("get", provider_uri).json()

            return provider_info["providerAddress"]
        except requests.exceptions.RequestException:
            pass

        return None

    @staticmethod
    @enforce_types
    def get_root_uri(service_endpoint: str) -> str:
        provider_uri = service_endpoint
        api_version = DataServiceProvider.get_api_version()
        if api_version in provider_uri:
            i = provider_uri.find(api_version)
            provider_uri = provider_uri[:i]
        parts = provider_uri.split("/")

        if len(parts) < 2:
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        if parts[-2] == "services":
            provider_uri = "/".join(parts[:-2])

        result = DataServiceProvider._remove_slash(provider_uri)

        if not result:
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        try:
            root_result = "/".join(parts[0:3])
            response = requests.get(root_result).json()
        except (requests.exceptions.RequestException, JSONDecodeError):
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        if "providerAddress" not in response:
            raise InvalidURL(
                f"Invalid Provider URL {service_endpoint}, no providerAddress."
            )

        return result

    @staticmethod
    @enforce_types
    def is_valid_provider(provider_uri: str) -> bool:
        try:
            DataServiceProvider.get_root_uri(provider_uri)
        except InvalidURL:
            return False

        return True

    @staticmethod
    @enforce_types
    def build_endpoint(service_name: str, provider_uri: str) -> Tuple[str, str]:
        provider_uri = DataServiceProvider.get_root_uri(provider_uri)
        service_endpoints = DataServiceProvider.get_service_endpoints(provider_uri)

        method, url = service_endpoints[service_name]
        return method, urljoin(provider_uri, url)

    @staticmethod
    @enforce_types
    def build_encrypt_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("encrypt", provider_uri)

    @staticmethod
    @enforce_types
    def build_initialize_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("initialize", provider_uri)

    @staticmethod
    @enforce_types
    def build_download_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("download", provider_uri)

    @staticmethod
    @enforce_types
    def build_compute_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("computeStatus", provider_uri)

    @staticmethod
    @enforce_types
    def build_compute_result_file_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("computeResult", provider_uri)

    @staticmethod
    @enforce_types
    def build_fileinfo(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("fileinfo", provider_uri)

    @staticmethod
    @enforce_types
    def write_file(
        response: Response,
        destination_folder: Union[str, bytes, os.PathLike],
        file_name: str,
    ) -> None:
        """
        Write the response content in a file in the destination folder.
        :param response: Response
        :param destination_folder: Destination folder, string
        :param file_name: File name, string
        :return: None
        """
        if response.status_code == 200:
            with open(os.path.join(destination_folder, file_name), "wb") as f:
                for chunk in response.iter_content(chunk_size=None):
                    f.write(chunk)
            logger.info(f"Saved downloaded file in {f.name}")
        else:
            logger.warning(f"consume failed: {response.reason}")

    @staticmethod
    @enforce_types
    def _send_compute_request(
        http_method: str,
        did: str,
        job_id: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
    ) -> Dict[str, Any]:
        compute_url = (
            f"{service_endpoint}"
            f"?signature={signature}"
            f"&documentId={did}"
            f"&consumerAddress={consumer_address}"
            f'&jobId={job_id or ""}'
        )
        logger.info(f"invoke compute endpoint with this url: {compute_url}")
        response = DataServiceProvider._http_method(http_method, compute_url)
        logger.debug(
            f"got provider execute response: {response.content} with status-code {response.status_code} "
        )
        if response.status_code != 200:
            raise Exception(response.content.decode("utf-8"))

        resp_content = json.loads(response.content.decode("utf-8"))
        if isinstance(resp_content, list):
            return resp_content[0]
        return resp_content

    @staticmethod
    @enforce_types
    def _get_file_name(response: Response) -> Optional[str]:
        try:
            return re.match(
                r"attachment;filename=(.+)", response.headers.get("content-disposition")
            )[1]
        except Exception as e:
            logger.warning(f"It was not possible to get the file name. {e}")
            return None

    @staticmethod
    @enforce_types
    def _prepare_compute_payload(
        did: str,
        consumer_address: str,
        service_id: int,
        order_tx_id: str,
        signature: Optional[str] = None,
        algorithm_did: Optional[str] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_tx_id: Optional[str] = None,
        algorithm_data_token: Optional[str] = None,
        output: Optional[dict] = None,
        input_datasets: Optional[list] = None,
        job_id: Optional[str] = None,
        userdata: Optional[dict] = None,
        algouserdata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        assert (
            algorithm_did or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        if algorithm_meta:
            assert isinstance(algorithm_meta, AlgorithmMetadata), (
                f"expecting a AlgorithmMetadata type "
                f"for `algorithm_meta`, got {type(algorithm_meta)}"
            )

        _input_datasets = []
        if input_datasets:
            for _input in input_datasets:
                assert _input.did, "The received dataset does not have a did."
                assert (
                    _input.transfer_tx_id
                ), "The received dataset does not have a transaction id."
                assert (
                    _input.service_id
                ), "The received dataset does not have a specified service id."
                if _input.did != did:
                    _input_datasets.append(_input.as_dictionary())

        payload = {
            "signature": signature,
            "documentId": did,
            "consumerAddress": consumer_address,
            "output": output or dict(),
            "jobId": job_id or "",
            "serviceId": service_id,
            "transferTxId": order_tx_id,
            "additionalInputs": _input_datasets or [],
            "userdata": userdata,
        }
        if algorithm_did:
            payload.update(
                {
                    "algorithmDid": algorithm_did,
                    "algorithmDataToken": algorithm_data_token,
                    "algorithmTransferTxId": algorithm_tx_id,
                }
            )

            if algouserdata:
                payload["algouserdata"] = algouserdata
        else:
            payload["algorithmMeta"] = algorithm_meta.as_dictionary()

        return payload

    @staticmethod
    @enforce_types
    def _http_method(method: str, *args, **kwargs) -> Optional[Union[Mock, Response]]:
        try:
            return getattr(DataServiceProvider._http_client, method)(*args, **kwargs)
        except Exception:
            logger.error(
                f"Error invoking http method {method}: args={str(args)}, kwargs={str(kwargs)}"
            )
            raise

    @staticmethod
    @enforce_types
    def check_single_file_info(file_url: str, provider_uri: str) -> bool:
        _, endpoint = DataServiceProvider.build_fileinfo(provider_uri)
        data = {"url": file_url}
        response = requests.post(endpoint, json=data)

        if response.status_code != 200:
            return False

        response = response.json()
        for file_info in response:
            return file_info["valid"]

        return False

    @staticmethod
    @enforce_types
    def check_asset_file_info(did: str, provider_uri: str) -> bool:
        if not did:
            return False
        _, endpoint = DataServiceProvider.build_fileinfo(provider_uri)
        data = {"did": did}
        response = requests.post(endpoint, json=data)

        if response.status_code != 200:
            return False

        response = response.json()
        for ddo_info in response:
            return ddo_info["valid"]

        return False


@enforce_types
def urljoin(*args) -> str:
    trailing_slash = "/" if args[-1].endswith("/") else ""

    return "/".join(map(lambda x: str(x).strip("/"), args)) + trailing_slash
