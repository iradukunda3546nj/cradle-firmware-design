🌐 Smart Cradle IoT Backend Architecture
📌 System Overview

The Smart Cradle system follows a structured IoT architecture:

Raspberry Pi (Edge Device)
        ↓
HTTP POST Requests (REST API)
        ↓
Server-Side PHP API
        ↓
MySQL Database
        ↓
Dashboard (HTML + CSS + JS)


The project is hosted under:

https://www.zolilabs.com/smart_cradle/

📂 Server Directory Structure

The deployed server folder:

smart_cradle/
│
├── api/
├── audio/
├── dashboard/
├── db/


Each folder has a specific engineering role.

🔹 1️⃣ audio/ – Media Storage Layer
Purpose:

Stores uploaded baby audio recordings.

Logic:

When the Raspberry Pi records audio:

WAV file recorded locally

Converted to MP3

Sent via HTTP POST to:

/smart_cradle/api/upload_audio.php


upload_audio.php saves file to:

smart_cradle/audio/


File is stored with timestamp-based naming:

$fileName = time() . "_" . basename($_FILES["audio"]["name"]);


This prevents filename collisions.

🔹 2️⃣ api/ – REST API Layer

This folder acts as the communication interface between:

Raspberry Pi (device)

Database

Dashboard

It contains:

✅ upload_audio.php
Function:

Receives multipart/form-data POST request.

Logic:

Reads $_FILES["audio"]

Moves file into /audio/

Returns JSON response:

{
  "status": "success",
  "audio_url": "https://www.zolilabs.com/smart_cradle/audio/xxxx.mp3"
}


This URL is later stored in the database.

✅ receive_data.php
Function:

Receives JSON POST request from Raspberry Pi.

Example Payload:
{
  "temperature": 28.3,
  "humidity": 50.2,
  "weight": 5,
  "presence": true,
  "audio_url": "https://..."
}

Logic:

Reads raw JSON body

Decodes into PHP array

Inserts into database table

Returns response

This file is the main IoT ingestion endpoint.

✅ data.php
Function:

Acts as API endpoint for frontend/dashboard.

Purpose:

Provides structured JSON data to the dashboard.

Flow:
Database → data.php → JSON → dashboard JavaScript → UI


This separates:

Data storage logic

Presentation logic

Good engineering separation of concerns.

🔹 3️⃣ db/ – Database Layer

Contains:

Database connection file

Configuration credentials

Possibly schema definitions

Role:

Central persistent storage

Stores:

Temperature

Humidity

Weight

Presence

Audio URL

Timestamp

Acts as historical data source.

🔹 4️⃣ dashboard/ – Visualization Layer
Technology Stack:

HTML

CSS

JavaScript (AJAX / Fetch API)

Logic:

JavaScript periodically requests:

/smart_cradle/api/data.php


Receives JSON response

Dynamically updates:

Temperature display

Humidity display

Weight display

Audio playback

Charts (if implemented)

This creates real-time monitoring interface.

🔁 Complete IoT Data Flow
🔹 Step 1 – Sensor Acquisition (Edge)

Raspberry Pi:

Reads DHT22

Reads HX711 weight

Records audio

Compresses to MP3

🔹 Step 2 – Data Upload

Two separate HTTP requests:

A) Multipart Upload
POST → upload_audio.php
Content-Type: multipart/form-data

B) JSON Upload
POST → receive_data.php
Content-Type: application/json

🔹 Step 3 – Server Processing

PHP validates input

Stores file

Inserts row into MySQL

🔹 Step 4 – Dashboard Retrieval

Frontend makes:

GET → data.php


Receives structured JSON for display.

🧠 Engineering Concepts Applied

This system demonstrates:

RESTful API design

Separation of backend and frontend logic

Edge-to-cloud communication

Multipart/form-data handling

JSON-based IoT communication

Server-side file handling

Database persistence

Web dashboard integration

🔐 Hosting Incident (Bot Protection)

At one point:

LiteSpeed Bot Protection blocked POST requests

IoT device could not solve reCAPTCHA

Server returned HTML instead of JSON

Solution:
Hosting provider whitelisted:

/smart_cradle/api/


This restored automated device communication.

This highlights the importance of:

Understanding server infrastructure

Recognizing HTTP vs application-level failures

Debugging IoT network layers

🏗 Architecture Classification

The Smart Cradle is now a:

Full-stack IoT System

It integrates:

Embedded systems

Real-time sensor acquisition

Digital signal processing

HTTP networking

REST APIs

Database systems

Web dashboards

Hosting infrastructure