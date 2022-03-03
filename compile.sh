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
       version: 0.8.10""" > brownie-config.yaml
brownie compile
rm brownie-config.yaml
cd ..

echo ""

echo "compile.sh: Done"

