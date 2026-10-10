package org.gep.mobile

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import android.util.Base64

object TokenVault {
 private const val ALIAS = "gep_device_token_v1"
 private const val PREF = "gep_secure_settings"
 private fun key(): SecretKey {
  val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
  (store.getKey(ALIAS, null) as? SecretKey)?.let { return it }
  val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
  generator.init(KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
   .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
   .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build())
  return generator.generateKey()
 }
 fun put(context: Context, value: String) {
  val cipher = Cipher.getInstance("AES/GCM/NoPadding")
  cipher.init(Cipher.ENCRYPT_MODE, key())
  val iv = Base64.encodeToString(cipher.iv, Base64.NO_WRAP)
  val ciphertext = Base64.encodeToString(cipher.doFinal(value.toByteArray(Charsets.UTF_8)),Base64.NO_WRAP)
  context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putString("token",iv+":"+ciphertext).apply()
 }
 fun get(context: Context): String? {
  val encoded=context.getSharedPreferences(PREF,Context.MODE_PRIVATE).getString("token",null) ?: return null
  return try {
   val parts=encoded.split(":",limit=2)
   val cipher=Cipher.getInstance("AES/GCM/NoPadding")
   cipher.init(Cipher.DECRYPT_MODE,key(),javax.crypto.spec.GCMParameterSpec(128,Base64.decode(parts[0],Base64.NO_WRAP)))
   String(cipher.doFinal(Base64.decode(parts[1],Base64.NO_WRAP)),Charsets.UTF_8)
  } catch (_: Exception) { null }
 }
 fun clear(context: Context) {
  context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().remove("token").apply()
 }
}
