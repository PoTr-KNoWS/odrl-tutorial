curl -L "https://sourceforge.net/projects/sunxacml/files/sunxacml/Version%201.2/sunxacml-1.2.zip/download" -o sunxacml.zip
tar -xf sunxacml.zip
cd sunxacml-1.2
java -cp "lib/sunxacml.jar;lib/samples.jar" SimplePDP sample/request/door-access.xml sample/policy/time-range.xml
