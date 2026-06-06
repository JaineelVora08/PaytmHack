import React, { useRef, useState } from "react";

export default function MicButton({ disabled, onRecording }) {
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [recording, setRecording] = useState(false);

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    recorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
      onRecording(blob);
    };

    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  return (
    <button
      className={recording ? "kv-mic kv-mic-recording" : "kv-mic"}
      disabled={disabled}
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onMouseLeave={() => recording && stopRecording()}
      onTouchStart={startRecording}
      onTouchEnd={stopRecording}
      type="button"
    >
      {recording ? "Release to Ask" : "Hold Mic"}
    </button>
  );
}
