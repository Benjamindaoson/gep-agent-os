package org.gep.mobile

import android.app.Activity
import android.os.Bundle
import android.content.Intent
import android.provider.Settings
import android.view.ViewGroup
import android.widget.*

class MainActivity:Activity(){
 override fun onCreate(savedInstanceState:Bundle?){
  super.onCreate(savedInstanceState)
  val prefs=getSharedPreferences("gep_settings",MODE_PRIVATE)
  val layout=LinearLayout(this).apply {
   orientation=LinearLayout.VERTICAL
   setPadding(34,38,34,20)
  }
  fun label(text:String) {layout.addView(TextView(this).apply {this.text=text;textSize=17f;setPadding(0,12,0,12)})}
  fun field(hint:String,value:String=""):EditText {
   val input=EditText(this).apply {this.hint=hint;setText(value);setSingleLine(true)}
   layout.addView(input);return input
  }
  fun button(text:String, callback:()->Unit){
   layout.addView(Button(this).apply {this.text=text;setOnClickListener{callback()}})
  }
  label("GEP Android Companion")
  label("Optional activity observation. No screen capture, location, contacts or keystroke access.")
  val server=field("HTTPS GEP URL",prefs.getString("server","")?:"")
  val token=field("Device token from GEP web portal")
  label("Step 1: Sign in to GEP in a browser; create a device token. Paste it here.")
  button("Save encrypted device token") {
   val url=server.text.toString().trim().trimEnd('/')
   val secret=token.text.toString().trim()
   if(!url.startsWith("https://") || secret.isEmpty()) {
    Toast.makeText(this,"HTTPS address and token required",Toast.LENGTH_LONG).show()
   } else {
    prefs.edit().putString("server",url).apply()
    TokenVault.put(this,secret)
    token.text.clear()
    Toast.makeText(this,"Saved locally",Toast.LENGTH_SHORT).show()
   }
  }
  button("Grant Android Usage Access") {
   startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
  }
  button("Sync now") {
   if(!UsageCollector.granted(this))Toast.makeText(this,"Grant Usage Access first",Toast.LENGTH_LONG).show()
   else androidx.work.WorkManager.getInstance(this)
     .enqueue(androidx.work.OneTimeWorkRequestBuilder<SyncWorker>().build())
  }
  button("Enable optional background sync") {
   if(!UsageCollector.granted(this))Toast.makeText(this,"Grant Usage Access first",Toast.LENGTH_LONG).show()
   else {SyncWorker.start(this);Toast.makeText(this,"Scheduled approximately every 15 minutes",Toast.LENGTH_LONG).show()}
  }
  button("Stop background sync") {SyncWorker.stop(this)}
  button("Disconnect this device") {
   SyncWorker.stop(this);TokenVault.clear(this)
   prefs.edit().remove("server").remove("last_sync").apply()
   Toast.makeText(this,"Disconnected; revoke token in web portal too",Toast.LENGTH_LONG).show()
  }
  val scroll=ScrollView(this)
  scroll.addView(layout);setContentView(scroll)
 }
}
