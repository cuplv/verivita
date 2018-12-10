1. IllegalStateException is
thrown to prevent programming errors such as calling {@link #prepare()},
__prepareAsync()__, or one of the overloaded __setDataSource__
methods in an invalid state. 

2. Calling
__setDataSource(FileDescriptor)__, or
__setDataSource(String)__, or
__setDataSource(Context, Uri)__, or
__setDataSource(FileDescriptor, long, long)__ transfers a
MediaPlayer object in the Idle state to the
Initialized state.
__An IllegalStateException is thrown if setDataSource() is called in any other state__

3. It is important to note that the Preparing state is a transient state, and the behavior
of calling any method with side effect while a MediaPlayer object is in the Preparing state is undefined.

4. <tr><td>prepare </p></td>
<td>{Initialized, Stopped} </p></td>
<td>{Idle, Prepared, Started, Paused, PlaybackCompleted, Error} </p></td>
<td>Successful invoke of this method in a valid state transfers the
object to the <em>Prepared</em> state. Calling this method in an
invalid state throws an IllegalStateException.</p></td></tr>

5. <tr><td>prepareAsync </p></td>
<td>{Initialized, Stopped} </p></td>
<td>{Idle, Prepared, Started, Paused, PlaybackCompleted, Error} </p></td>
<td>Successful invoke of this method in a valid state transfers the
object to the <em>Preparing</em> state. Calling this method in an
invalid state throws an IllegalStateException.</p></td></tr>

6. <tr><td>setDataSource </p></td>
    <td>{Idle} </p></td>
    <td>{Initialized, Prepared, Started, Paused, Stopped, PlaybackCompleted,
         Error} </p></td>
    <td>Successful invoke of this method in a valid state transfers the
        object to the <em>Initialized</em> state. Calling this method in an
        invalid state throws an IllegalStateException.</p></td></tr>

7. __prepare()__, __prepareAsync()__:
Prepares the player for playback, synchronously.
After setting the datasource and the display surface, you need to either
call prepare() or prepareAsync(). For files, it is OK to call prepare(),
which blocks until MediaPlayer is ready for playback.
@throws IllegalStateException if it is called in an invalid state

8. __stop()__:
Stops playback after playback has been stopped or paused
@throws IllegalStateException if the internal player engine has not been
initialized

9. __pause()__:
Pause playback. Call start() to resume.
@throws IllegalStateException if the internal player engine has not been
initialized.

10. __start()__:
Starts or resumes playback. If playback had previously been paused,
playback will continue from where it was paused. If playback had
been stopped, or never started before, playback will start at the
beginning.
@throws IllegalStateException if it is called in an invalid state

11. __isPlaying()__: 
Checks whether the MediaPlayer is playing.
@return true if currently playing, false otherwise
@throws IllegalStateException if the internal player engine has not been
initialized or has been released.

12. __seekTo()__
Seeks to specified time position.
@param msec the offset in milliseconds from the start to seek to
@throws IllegalStateException if the internal player engine has not been
initialized

https://github.com/WhisperSystems/Signal-Android/issues/5222

https://github.com/WhisperSystems/Signal-Android/pull/5303

https://github.com/WhisperSystems/Signal-Android/issues/3004

https://github.com/libgdx/libgdx/pull/3399


https://github.com/AntennaPod/AntennaPod/pull/1306



https://github.com/zom/Zom-Android/issues/10