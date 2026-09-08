"""
TimeMeshin Cloud Web Application
Drop-in Cloud App for Google Cloud Run, Hugging Face Spaces, Render, Railway, and AWS.
Provides web-based drag-and-drop chat ingestion, noise filtering, and interactive (S x T) Matrix scrubbing.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from timemeshin.ingestion.folder_watcher import FolderWatcher
from timemeshin.client import TimeMeshinClient

# Initialize app
app = FastAPI(
    title="TimeMeshin Cloud Context Engine",
    description="Deterministic Spatio-Temporal (S x T) Video-Scrubber Memory Engine",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared cloud storage paths
CLOUD_DB_PATH = os.environ.get("TIMEMESHIN_DB", "cloud_timeline.db")
CLOUD_DROPZONE = Path(os.environ.get("TIMEMESHIN_DROPZONE", "cloud_dropzone"))
CLOUD_MATRIX_JSON = Path(os.environ.get("TIMEMESHIN_MATRIX_JSON", "cloud_matrix.json"))

CLOUD_DROPZONE.mkdir(parents=True, exist_ok=True)

watcher = FolderWatcher(
    watch_dir=str(CLOUD_DROPZONE),
    db_path=CLOUD_DB_PATH,
    matrix_output_path=str(CLOUD_MATRIX_JSON)
)
client = TimeMeshinClient(db_path=CLOUD_DB_PATH)


@app.get("/", response_class=HTMLResponse)
async def serve_cloud_ui():
    """Serves the complete interactive Light-Theme Web UI with drag-and-drop dropzone."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMeshin Cloud — Spatio-Temporal Matrix</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f8fafc; color: #1e293b; }
    .card-committed { border-left: 4px solid #10b981; background: #ffffff; }
    .card-future { opacity: 0.25; filter: grayscale(80%); }
    .timeline-scrubber::-webkit-slider-thumb {
      -webkit-appearance: none; appearance: none;
      width: 22px; height: 22px; border-radius: 50%;
      background: #2563eb; cursor: pointer; border: 3px solid #ffffff;
      box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }
  </style>
</head>
<body class="p-4 md:p-8">

  <div class="max-w-7xl mx-auto mb-6 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black text-2xl shadow-md">
          ⏳
        </div>
        <div>
          <h1 class="text-2xl font-black text-slate-800 tracking-tight">TimeMeshin Cloud</h1>
          <p class="text-xs text-slate-500 font-medium">Spatio-Temporal Memory Engine (<span class="text-blue-600 font-bold">T-Axis →</span> &times; <span class="text-emerald-600 font-bold">S-Axis ↓</span>)</p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
          <i class="fa-solid fa-cloud-arrow-up mr-1.5"></i> Cloud Active
        </span>
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
          <i class="fa-solid fa-filter mr-1.5"></i> Noise Filter Gated
        </span>
      </div>
    </div>

    <!-- Web Drag-and-Drop Cloud Upload Zone -->
    <div id="drop-area" class="border-2 border-dashed border-blue-300 hover:border-blue-500 bg-blue-50/50 hover:bg-blue-50 transition rounded-xl p-6 text-center cursor-pointer mb-6" onclick="document.getElementById('file-input').click()">
      <input id="file-input" type="file" class="hidden" multiple onchange="handleFiles(this.files)" accept=".html,.htm,.pdf,.md,.txt,.json,.csv">
      <div class="flex flex-col items-center justify-center gap-2">
        <i class="fa-solid fa-cloud-arrow-up text-3xl text-blue-600"></i>
        <p class="text-sm font-bold text-slate-700">Drag and Drop chat exports here, or <span class="text-blue-600 underline">browse files</span></p>
        <p class="text-xs text-slate-400">Supports .html, .pdf, .md, .txt, .json, .csv (Automated Noise Filtering + Timeline Alignment)</p>
      </div>
      <div id="upload-status" class="text-xs font-bold text-blue-700 mt-2 hidden"></div>
    </div>

    <!-- Playhead Scrubber Bar -->
    <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
      <div class="flex justify-between items-center mb-2">
        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">
          <i class="fa-solid fa-video text-blue-600 mr-1"></i> Playhead Position ($t \le T$):
        </span>
        <span id="playhead-label" class="text-sm font-black text-blue-700 bg-blue-50 px-3 py-0.5 rounded-full border border-blue-200">
          Latest
        </span>
      </div>
      <input id="scrubber-slider" type="range" min="0" max="1" value="1" class="timeline-scrubber w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" oninput="onScrub(this.value)">
      <div class="flex justify-between text-[11px] text-slate-400 mt-1.5 font-medium">
        <span>T_0 (Genesis)</span>
        <span>◄ Drag to scrub timeline backwards & forwards ►</span>
        <span>T_Current</span>
      </div>
    </div>
  </div>

  <!-- S x T Matrix Grid -->
  <div class="max-w-7xl mx-auto overflow-x-auto bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
    <div class="min-w-[900px]">
      <div class="grid grid-cols-12 gap-4 pb-4 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase">
        <div class="col-span-3 text-slate-700 flex items-center gap-1.5">
          <i class="fa-solid fa-layer-group text-emerald-600"></i> Topic Swimlane (S ↓)
        </div>
        <div class="col-span-9 flex items-center justify-between text-blue-700">
          <span><i class="fa-solid fa-arrow-right mr-1"></i> Chronological Timeline Events (T →)</span>
          <span class="text-[11px] font-normal text-slate-400">Events gated by Playhead</span>
        </div>
      </div>
      <div id="swimlanes-container" class="divide-y divide-slate-100">
        <!-- Injected via JavaScript -->
      </div>
    </div>
  </div>

  <!-- Ground Truth Active State Drawer -->
  <div class="max-w-7xl mx-auto bg-white rounded-xl shadow-sm border border-slate-200 p-6">
    <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
      <i class="fa-solid fa-bolt text-amber-500"></i> Active Ground-Truth State at Playhead:
    </h3>
    <div id="active-state-summary" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3"></div>
  </div>

  <script>
    let matrixData = { topics: [], timeline: [], events: [] };
    let currentPlayheadIdx = 0;

    async function fetchMatrix() {
      try {
        const resp = await fetch("/api/matrix");
        if (resp.ok) {
          matrixData = await resp.json();
          const maxIdx = Math.max(1, matrixData.timeline.length);
          document.getElementById("scrubber-slider").max = maxIdx;
          document.getElementById("scrubber-slider").value = maxIdx;
          currentPlayheadIdx = maxIdx;
          renderMatrix();
        }
      } catch (err) {
        console.error("Error fetching matrix:", err);
      }
    }

    async function handleFiles(files) {
      if (!files.length) return;
      const statusDiv = document.getElementById("upload-status");
      statusDiv.classList.remove("hidden");
      statusDiv.innerText = `Uploading and ingesting ${files.length} document(s)...`;

      for (let f of files) {
        const formData = new FormData();
        formData.append("file", f);
        try {
          const resp = await fetch("/api/upload", { method: "POST", body: formData });
          const res = await resp.json();
          console.log("Uploaded:", res);
        } catch (e) {
          console.error("Upload error:", e);
        }
      }

      statusDiv.innerText = "✓ Ingestion complete! Timeline updated.";
      setTimeout(() => statusDiv.classList.add("hidden"), 3000);
      await fetchMatrix();
    }

    function renderMatrix() {
      const container = document.getElementById("swimlanes-container");
      container.innerHTML = "";
      const activeState = {};

      const currentTimestamp = matrixData.timeline[currentPlayheadIdx - 1] || "Genesis";
      document.getElementById("playhead-label").innerText = currentTimestamp;

      const topics = matrixData.topics && matrixData.topics.length ? matrixData.topics : [
        "Database & Storage", "Auth & Security", "Architecture & Core", "Budget & Operations", "UI & Frontend"
      ];

      topics.forEach(topic => {
        const row = document.createElement("div");
        row.className = "grid grid-cols-12 gap-4 py-4 items-center";

        const labelCol = document.createElement("div");
        labelCol.className = "col-span-3 pr-2";
        labelCol.innerHTML = `
          <div class="font-bold text-slate-800 text-sm flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
            ${topic}
          </div>
        `;

        const eventsCol = document.createElement("div");
        eventsCol.className = "col-span-9 flex items-center gap-3 overflow-x-auto py-1";

        const topicEvents = (matrixData.events || []).filter(e => e.topic === topic);

        if (topicEvents.length === 0) {
          eventsCol.innerHTML = `<span class="text-xs text-slate-300 italic">No events in this rack</span>`;
        } else {
          topicEvents.forEach(e => {
            const eventTimeIdx = matrixData.timeline.indexOf(e.timestamp) + 1;
            const isFuture = eventTimeIdx > currentPlayheadIdx;

            const card = document.createElement("div");
            card.className = `flex-shrink-0 w-64 p-3 rounded-lg border shadow-xs transition-all duration-200 ${
              isFuture ? 'card-future bg-slate-50 border-slate-200' : 'card-committed border-slate-200 shadow-sm'
            }`;

            if (!isFuture) {
              activeState[e.entity] = { attribute: e.attribute, value: e.new_value, updated: e.timestamp };
            }

            card.innerHTML = `
              <div class="flex justify-between items-center mb-1">
                <span class="text-[10px] font-bold text-slate-500"><i class="fa-regular fa-clock mr-1"></i>${e.timestamp}</span>
                <span class="text-[9px] font-bold px-1.5 py-0.5 rounded ${isFuture ? 'bg-slate-200 text-slate-600' : 'bg-emerald-100 text-emerald-800'}">
                  ${isFuture ? 'FUTURE' : 'COMMITTED'}
                </span>
              </div>
              <div class="text-xs font-black text-slate-800">${e.entity} ➔ <span class="text-blue-600">${e.new_value}</span></div>
              <div class="text-[11px] text-slate-500 mt-1 line-clamp-2" title="${e.causal_reason}">
                <span class="font-medium text-slate-600">Why:</span> ${e.causal_reason || e.raw_text}
              </div>
            `;
            eventsCol.appendChild(card);
          });
        }

        row.appendChild(labelCol);
        row.appendChild(eventsCol);
        container.appendChild(row);
      });

      renderStateSummary(activeState);
    }

    function renderStateSummary(state) {
      const summaryDiv = document.getElementById("active-state-summary");
      summaryDiv.innerHTML = "";
      const keys = Object.keys(state);
      if (keys.length === 0) {
        summaryDiv.innerHTML = `<div class="col-span-4 text-xs text-slate-400 italic">No active entities at this playhead.</div>`;
        return;
      }
      keys.forEach(k => {
        const item = state[k];
        const card = document.createElement("div");
        card.className = "p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs";
        card.innerHTML = `
          <div class="text-[11px] font-bold text-slate-500 uppercase">${k}</div>
          <div class="text-sm font-black text-slate-800 mt-0.5 text-blue-700">${item.value}</div>
          <div class="text-[10px] text-slate-400 mt-1">Updated: ${item.updated}</div>
        `;
        summaryDiv.appendChild(card);
      });
    }

    function onScrub(val) {
      currentPlayheadIdx = parseInt(val);
      renderMatrix();
    }

    // Drag-and-drop event listeners
    const dropArea = document.getElementById("drop-area");
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); }, false);
    });
    dropArea.addEventListener('drop', e => {
      const dt = e.dataTransfer;
      handleFiles(dt.files);
    });

    window.addEventListener("DOMContentLoaded", fetchMatrix);
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


@app.post("/api/upload")
async def upload_chat_file(file: UploadFile = File(...)):
    """Uploads and processes a chat export, filtering out-of-context noise in the cloud."""
    target_path = CLOUD_DROPZONE / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ingested = watcher.process_file(target_path)
    return {
        "status": "success",
        "filename": file.filename,
        "events_ingested": ingested
    }


@app.get("/api/matrix")
async def get_matrix():
    """Returns the current (S x T) Spatio-Temporal Matrix data."""
    matrix = watcher.export_spatio_temporal_matrix()
    return JSONResponse(content=matrix)


@app.get("/api/scrub")
async def scrub_playhead(playhead: str = Query(..., description="Timestamp to scrub playhead to")):
    """Scrubs playhead and returns exact ground-truth state."""
    state = client.scrub(playhead=playhead)
    return {
        "playhead": playhead,
        "ground_truth_state": state
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting TimeMeshin Cloud App on http://0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)