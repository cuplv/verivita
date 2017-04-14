BASE_DIR=/home/s/Documents/data/monkey_traces/
#python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace ${BASE_DIR}$1 --filter_class android.app.Fragment --filter_method "java.lang.String getString(int)"
python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace ${BASE_DIR}$1 --filter_class android.app.Fragment --filter_method "void startActivity(android.content.Intent)"
