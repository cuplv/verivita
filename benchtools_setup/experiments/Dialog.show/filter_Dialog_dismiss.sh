BASE_DIR=/
#python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace ${BASE_DIR}$1 --filter_class android.app.Fragment --filter_method "java.lang.String getString(int)"
#void android.app.Dialog.dismiss()
python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace ${BASE_DIR}$1 --filter_class android.app.Dialog --filter_method "void show()"
