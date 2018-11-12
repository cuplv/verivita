#!/bin/sh

echo "COMMAND LINE: " "$@"
echo "BENCHTOOLS_PARAMS: $BENCHTOOLS_PARAMS"
echo "BENCHTOOLS_INSTANCE: $BENCHTOOLS_INSTANCE"

CB_PATH=${BENCHTOOLS_PARAMS%%;*}
str3=${BENCHTOOLS_PARAMS##*;}
temp=${BENCHTOOLS_PARAMS#$CB_PATH;}
SPECS=${temp#;$str3}

echo ${BENCHTOOLS_PARAMS}
echo ${CB_PATH}
echo ${SPECS}


echo "python ${CB_PATH}/cbverifier/driver.py -t ${BENCHTOOLS_INSTANCE} -s ${SPECS} -m ic3 -z -q 300 -n ${NUXMV_PATH}"
python "${CB_PATH}/cbverifier/driver.py" -t ${BENCHTOOLS_INSTANCE} -s "${SPECS}" -m ic3 -z -q 300 -n ${NUXMV_PATH}
