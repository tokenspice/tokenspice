echo "compile.sh: Install 3rd party libs"
brownie pm install OpenZeppelin/openzeppelin-contracts@2.1.1
brownie pm install OpenZeppelin/openzeppelin-contracts@4.0.0
brownie pm install OpenZeppelin/openzeppelin-contracts@4.2.0
brownie pm install GNSPS/solidity-bytes-utils@0.8.0

echo "compile.sh: Compile sol057/..."
cd sol057
echo """compiler:
   solc:
       version: 0.5.7""" > brownie-config.yaml
brownie compile
rm brownie-config.yaml
cd ..

echo ""

echo "compile.sh: Compile sol080/..."
cd sol080
echo """compiler:
   solc:
       version: 0.8.0""" > brownie-config.yaml
brownie compile
rm brownie-config.yaml
cd ..

echo ""

echo "compile.sh: Done"

