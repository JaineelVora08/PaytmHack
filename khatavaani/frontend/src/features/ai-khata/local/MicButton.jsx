import React, { useRef, useState } from "react";

const MIME_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];

function supportedMimeType() {
  if (typeof MediaRecorder === "undefined") {
    return "";
  }
  return MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

export default function MicButton({ disabled, onError, onRecording }) {
  const chunksRef = useRef([]);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const [recording, setRecording] = useState(false);

  async function startRecording() {
    if (disabled || recording) {
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      onError?.("Mic recording is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = supportedMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      chunksRef.current = [];
      streamRef.current = stream;
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data?.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        mediaRecorderRef.current = null;

        const type = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        chunksRef.current = [];

        if (blob.size > 0) {
          onRecording(blob);
        } else {
          onError?.("No audio was captured. Please try again.");
        }
      };

      recorder.start(250);
      setRecording(true);
    } catch (error) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      mediaRecorderRef.current = null;
      setRecording(false);
      onError?.(error?.name === "NotAllowedError" ? "Please allow microphone access." : "Could not start recording.");
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recording || !recorder) {
      return;
    }

    setRecording(false);
    if (recorder.state !== "inactive") {
      recorder.stop();
    }
  }

  function handleClick() {
    if (recording) {
      stopRecording();
      return;
    }
    startRecording();
  }

  return (
    <button
      aria-pressed={recording}
      className={recording ? "kv-mic kv-mic-recording" : "kv-mic"}
      disabled={disabled}
      onClick={handleClick}
      type="button"
    >
      <span>{recording ? "Send voice question" : "Start voice question"}</span>
      <small>{recording ? "Recording now" : "Tap once, then tap again"}</small>
    </button>
  );
}
