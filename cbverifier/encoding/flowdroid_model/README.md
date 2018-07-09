# Hardcoded Android callback control-flow model of FlowDroid

# Description of the FlowDroid model

FlowDroid encodes the lifecylce of each Android component adding a new class encoding a "dummy" main method.
The (AndroiodEntryPointCreator)[https://github.com/secure-software-engineering/FlowDroid/blob/a1438c2b38a6ba453b91e38b2f7927b6670a2702/soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/AndroidEntryPointCreator.java] contains the code that generate the "dummy" main method and hence the lifecycle for each Android component, such as `Activity`, `Fragment`, ecc...


Flowdroid encodes:
- The lifecycle of the application component


- The lifecycle of each other component of the app.

The components are: Activity, Service, GCMBaseIntentService, GCMListenerService, ServiceConnection, BroadcastReceiver, ContentProvider, Plain.

`Plain`: no order of execution, assume an arbitrary order of callback execution in the component.

At line 334 of (AndroiodEntryPointCreator.java)[https://github.com/secure-software-engineering/FlowDroid/blob/a1438c2b38a6ba453b91e38b2f7927b6670a2702/soot-infoflow/src/soot/jimple/infoflow/entryPointCreators/AndroidEntryPointCreator.java]
```java
        // Generate the lifecycles for the different kinds of Android
        // classes
        switch (componentType) {
        case Activity:
          generateActivityLifecycle(callbackSigs, currentClass, endClassStmt, classLocal,
              beforeComponentStmt);
          break;
        case Service:
        case GCMBaseIntentService:
        case GCMListenerService:
          generateServiceLifecycle(callbackSigs, currentClass, endClassStmt, classLocal);
          break;
        // case Fragment:
        // generateFragmentLifecycle(entry.getValue(), currentClass,
        // endClassStmt, classLocal);
        // break;
        case ServiceConnection:
          generateServiceConnetionLifecycle(callbackSigs, currentClass, endClassStmt, classLocal);
          break;
        case BroadcastReceiver:
          generateBroadcastReceiverLifecycle(callbackSigs, currentClass, endClassStmt, classLocal);
          break;
        case ContentProvider:
          generateContentProviderLifecycle(callbackSigs, currentClass, endClassStmt, classLocal);
          break;
        case Plain:
          // Allow the complete class to be skipped
          createIfStmt(endClassStmt);

          NopStmt beforeClassStmt = Jimple.v().newNopStmt();
          body.getUnits().add(beforeClassStmt);
          for (SootMethod currentMethod : plainMethods.values()) {
            if (!currentMethod.isStatic() && classLocal == null) {
              logger.warn("Skipping method {} because we have no instance", currentMethod);
              continue;
            }

            // Create a conditional call on the current method
            NopStmt thenStmt = Jimple.v().newNopStmt();
            createIfStmt(thenStmt);
            buildMethodCall(currentMethod, body, classLocal, generator);
            body.getUnits().add(thenStmt);

            // Because we don't know the order of the custom
            // statements,
            // we assume that you can loop arbitrarily
            createIfStmt(beforeClassStmt);
          }
          break;
        }
```

# Fragment lifecycle

Generated inside the `generateActivityLifecycle` calling the `generateFragmentLifecycle` method.

The fragment lifecycle starts just after the call to `AndroidEntryPointConstants.ACTIVITY_ONATTACHFRAGMENT`.
It attach the specific fragment to the specific activity. There is a non-deterministic jump after `AndroidEntryPointConstants.ACTIVITY_ONATTACHFRAGMENT`. It can either enter the fragment lifecycle or 

Then the activity lifecycle can 
- `AndroidEntryPointConstants.FRAGMENT_ONATTACH`
- `AndroidEntryPointConstants.FRAGMENT_ONCREATEVIEW`
- `AndroidEntryPointConstants.FRAGMENT_ONVIEWCREATED`
- `AndroidEntryPointConstants.FRAGMENT_ONACTIVITYCREATED`
- `AndroidEntryPointConstants.FRAGMENT_ONSTART`
- `AndroidEntryPointConstants.FRAGMENT_ONRESUME`
- `AndroidEntryPointConstants.FRAGMENT_ONPAUSE`
- `AndroidEntryPointConstants.FRAGMENT_ONPAUSE` -> `AndroidEntryPointConstants.FRAGMENT_ONRESUME`
- `AndroidEntryPointConstants.FRAGMENT_ONSAVEINSTANCESTATE`
- `AndroidEntryPointConstants.FRAGMENT_ONSTOP`
- `AndroidEntryPointConstants.FRAGMENT_ONSTOP` -> `AndroidEntryPointConstants.FRAGMENT_ONCREATEVIEW`
- `AndroidEntryPointConstants.FRAGMENT_ONSTOP` -> `AndroidEntryPointConstants.FRAGMENT_ONSTART`
- `AndroidEntryPointConstants.FRAGMENT_ONDESTROYVIEW`
- `AndroidEntryPointConstants.FRAGMENT_ONDESTROYVIEW` -> `AndroidEntryPointConstants.FRAGMENT_ONCREATEVIEW`
- `AndroidEntryPointConstants.FRAGMENT_ONDESTROY` 
- `AndroidEntryPointConstants.FRAGMENT_ONDETACH`
- `AndroidEntryPointConstants.FRAGMENT_ONDETACH` -> - `AndroidEntryPointConstants.FRAGMENT_ONATTACH`




Q: can you have a fragment inside a fragment?
Yes, and they really screw up with that!

Q: can the fragment lifecycle callback interleave with each other?
Yes, and they really screw up with that!

Q: can the activity lifecycle callback interleave with each other?
Yes, and they really screw up with that!

