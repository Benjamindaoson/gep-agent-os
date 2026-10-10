package org.gep.mobile

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.os.Process
import android.os.Build
import org.json.JSONArray
import org.json.JSONObject

object UsageCollector {
 fun granted(context: Context): Boolean {
  val ops=context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
  return ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS,Process.myUid(),context.packageName)==AppOpsManager.MODE_ALLOWED
 }
 /** Reconstruct foreground intervals within a short fixed window. No screen contents or keystrokes. */
 fun collect(context: Context, start: Long, end: Long): JSONArray {
  require(end>start && end-start<=24L*3600*1000)
  if(!granted(context))throw SecurityException("Usage access not granted")
  val service=context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
  // Query from start: some sessions crossing the window boundary may be absent.
  // We report observed intervals only; no fabricated continuity.
  val events=service.queryEvents(start,end)
  val opened=mutableMapOf<String,Long>()
  val durations=mutableMapOf<String,Long>()
  val event=UsageEvents.Event()
  while(events.hasNextEvent()){
   events.getNextEvent(event)
   val app=event.packageName ?: continue
   when(event.eventType){
    UsageEvents.Event.MOVE_TO_FOREGROUND,UsageEvents.Event.ACTIVITY_RESUMED ->
      if(!opened.containsKey(app))opened[app]=event.timeStamp
    UsageEvents.Event.MOVE_TO_BACKGROUND,UsageEvents.Event.ACTIVITY_PAUSED -> {
     val began=opened.remove(app) ?: continue
     durations[app]=(durations[app]?:0)+(event.timeStamp-began).coerceAtLeast(0)
    }
   }
  }
  for((app,began) in opened) durations[app]=(durations[app]?:0)+(end-began).coerceAtLeast(0)
  val arr=JSONArray()
  for((app,ms) in durations) if(ms>0 && ms<=end-start)
    arr.put(JSONObject().put("start_ms",start).put("end_ms",end)
     .put("package",app).put("foreground_ms",ms))
  return arr
 }
}
