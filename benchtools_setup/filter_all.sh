#!/bin/bash
#rm ./instances/*.txt 2>/dev/null
#find -L ~/Documents/data/monkey_traces/ -name "*repaired" > ./instances/allTraces.txt #overwrite old one
#find ~/Documents/data/monkey_traces/ -name "trace-*" >> ./instances/allTraces.txt #append

TOTAL_NUMBER_TRACES=$(cat ./instances/allTraces.txt |wc -l)
echo "total traces: ${TOTAL_NUMBER_TRACES}"

#cat ./instances/allTraces.txt |shuf |head -n 1 > ./instances/traces_to_process.txt
cat ./instances/allTraces.txt |sort > ./instances/traces_to_process.txt
for TRACE in `cat ./instances/traces_to_process.txt`
do
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.FragmentTransaction --filter_method "int commit()" >> ./instances/FragmentTrans.commit.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.os.AsyncTask --filter_method "android.os.AsyncTask execute(java.lang.Object[])" >> ./instances/AsyncTask.execute.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.os.AsyncTask --filter_method "android.os.AsyncTask executeOnExecutor(java.util.concurrent.Executor,java.lang.Object[])" >> ./instances/AsyncTask.executeOnExecutor.txt)&

	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "android.content.res.Resources getResources()" >> ./instances/Fragment.getResources.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "android.content.res.Resources getResources()" >>./instances/Fragmentv4.getResources.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "java.lang.CharSequence getText(int)" >> ./instances/Fragmentv4.getText.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "java.lang.CharSequence getText(int)" >> ./instances/Fragment.getText.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.media.MediaPlayer --filter_method "void start()" >> ./instances/MediaPlayer.start.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.content.res.TypedArray --filter_method "void recycle()" >> ./instances/TypedArray.recycle.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "java.lang.String getString(int)" >> ./instances/Fragment.getString.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "java.lang.String getString(int)" >> ./instances/Fragmentv4.getString.txt)&

	# start activity
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "void startActivity(android.content.Intent)" >> ./instances/Fragment.startActivity.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "void startActivity(android.content.Intent)" >> ./instances/Fragmentv4.startActivity.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "void startActivity(android.content.Intent,android.os.Bundle)" >> ./instances/Fragment.startActivity.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "void startActivity(android.content.Intent,android.os.Bundle)" >> ./instances/Fragmentv4.startActivity.txt)&

	# start activity for result (goes into startActivity traces)
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "void startActivityForResult(android.content.Intent,int)" >> ./instances/Fragment.startActivity.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "void startActivityForResult(android.content.Intent,int)" >> ./instances/Fragmentv4.startActivity.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "void startActivityForResult(android.content.Intent,int,android.os.Bundle)" >> ./instances/Fragment.startActivity.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "void startActivityForResult(android.content.Intent,int,android.os.Bundle)" >> ./instances/Fragmentv4.startActivity.txt)&


	# getLoaderManager
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "android.app.LoaderManager getLoaderManager()" >> ./instances/Fragment.getLoaderManager.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "android.support.v4.app.LoaderManager getLoaderManager()" >> ./instances/Fragment.getLoaderManager.txt)&


	#dismiss show
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Dialog --filter_method "void dismiss()" >> ./instances/Dialog.dismiss.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Dialog --filter_method "void show()" >> ./instances/Dialog.show.txt)&

	#setArguments
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.app.Fragment --filter_method "void setArguments(android.os.Bundle)" >> ./instances/Fragment.setArguments.txt)&
	(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.support.v4.app.Fragment --filter_method "void setArguments(android.os.Bundle)" >> ./instances/Fragment.setArguments.txt)&
	wait
done


#PROCESSTRACES=$(echo $ALLTRACES |shuf |head -n 10)

#echo $PROCESSTRACES
#	wait
#done
#
#for TRACE in `cat ./instances/traces_to_process.txt`
#do
	#(python ~/Documents/source/TraceRunner/utils/ProtoConverter/filterProto.py --trace $TRACE --filter_class android.media.MediaPlayer --filter_method "void start()" >> ./instances/MediaPlayer.start.txt)&

