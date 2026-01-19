package com.reader.lotm.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "chapters")
data class ChapterEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val title: String,
    val content: String? = null,
    val url: String? = null,
    @ColumnInfo(name = "order_index")
    val orderIndex: Int? = null,
    @ColumnInfo(name = "book_id")
    val bookId: String? = null
)
