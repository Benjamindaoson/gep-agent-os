package org.gep.mobile

import android.content.Context
import androidx.work.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit

class SyncWorker(context:Context, params:WorkerParameters):Worker(context,params) {
 override fun doWork():Result {
  val prefs=applicationContext.getSharedPreferences("gep_settings",Context.MODE_PRIVATE)
  val base=prefs.getString("server",null) ?: return Result.failure()
  if(!base.startsWith("https://"))return Result.failure()
  val token=TokenVault.get(applicationContext) ?: return Result.failure()
  if(!UsageCollector.granted(applicationContext))return Result.failure()
  val end=System.currentTimeMillis()
  val previous=prefs.getLong("last_sync",0L)
  // Keep each reporting interval <=24h; backfill gradually after a long offline period.
  val start=if(previous==0L) end-15L*60*1000 else previous
  if(start>=end) return Result.success()
  val upper=minOf(end,start+24L*3600*1000)
  return try {
   val body=JSONObject().put("events",UsageCollector.collect(applicationContext,start,upper)).toString()
   val conn=(URL(base.trimEnd('/')+"/api/mobile/usage").openConnection() as HttpURLConnection)
   conn.requestMethod="POST";conn.connectTimeout=15000;conn.readTimeout=15000
   conn.setRequestProperty("Authorization","Bearer "+token)
   conn.setRequestProperty("Content-Type","application/json")
   conn.doOutput=true
   conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
   val status=conn.responseCode
   conn.disconnect()
   if(status in 200..299){
    prefs.edit().putLong("last_sync",upper).apply()
    Result.success()
   } else if(status==401 || status==403 || status==422)Result.failure()
   else Result.retry()
  } catch (_: Exception) { Result.retry() }
 }
 companion object {
  fun start(context:Context){
   val constraints=Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
   val request=PeriodicWorkRequestBuilder<SyncWorker>(15,TimeUnit.MINUTES)
     .setConstraints(constraints).build()
   WorkManager.getInstance(context).enqueueUniquePeriodicWork(
     "gep_optional_usage_sync",ExistingPeriodicWorkPolicy.KEEP,request)
  }
  fun stop(context:Context){
   WorkManager.getInstance(context).cancelUniqueWork("gep_optional_usage_sync")
  }
 }
}
