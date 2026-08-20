package com.example.offlinetranslator.ai.translation

import java.io.File
import java.util.regex.Pattern

class SimpleTokenizer(private val vocabFile: File?) {

    private val tokenToId = HashMap<String, Long>()
    private val idToToken = HashMap<Long, String>()

    init {
        loadVocab()
    }

    private fun loadVocab() {
        // Default special tokens
        addToken("<pad>", 0L)
        addToken("</s>", 1L)
        addToken("<unk>", 2L)

        if (vocabFile != null && vocabFile.exists()) {
            try {
                vocabFile.forEachLine { line ->
                    val parts = line.split(" ", "\t", ":")
                    if (parts.size >= 2) {
                        val token = parts[0].trim()
                        val id = parts[1].trim().toLongOrNull()
                        if (id != null) {
                            addToken(token, id)
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun addToken(token: String, id: Long) {
        tokenToId[token] = id
        idToToken[id] = token
    }

    fun encode(text: String): LongArray {
        val words = text.trim().split(Pattern.compile("\\s+"))
        val ids = mutableListOf<Long>()
        for (word in words) {
            val formatted = " $word"
            val id = tokenToId[formatted] ?: tokenToId[word] ?: tokenToId["<unk>"] ?: 2L
            ids.add(id)
        }
        ids.add(1L) // </s> EOS token
        return ids.toLongArray()
    }

    fun decode(tokenIds: LongArray): String {
        val sb = StringBuilder()
        for (id in tokenIds) {
            if (id == 0L || id == 1L || id == 2L) continue // Skip pad, eos, unk
            val token = idToToken[id]
            if (token != null) {
                if (token.startsWith(" ")) {
                    sb.append(" ").append(token.substring(1))
                } else {
                    sb.append(token)
                }
            }
        }
        return sb.toString().trim()
    }
}
