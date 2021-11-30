from util import globaltokens


def test_OCEAN():
    assert globaltokens.OCEANtoken().symbol() == "OCEAN"
    assert globaltokens.OCEAN_address()[:2] == "0x"
