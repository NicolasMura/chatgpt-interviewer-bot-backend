import { Component } from '@angular/core';

@Component({
  standalone: true,
  imports: [],
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  mediaRecorder!: MediaRecorder;
  isRecording = false;

  toggleRecording(): void {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      this.startRecording();
    }
  }

  startRecording(): void {
    console.log('start');
    const mediaConstraints = {
      video: false,
      audio: true,
    };

    navigator.mediaDevices
      .getUserMedia(mediaConstraints)
      .then(this.processAudioStream.bind(this))
      .catch((err) => {
        console.error(`An error occurred: ${err}`);
      });
  }

  processAudioStream(stream: MediaStream): void {
    this.isRecording = true;
    this.mediaRecorder = new MediaRecorder(stream);
    this.mediaRecorder.start();

    const audioChunks: Blob[] = [];
    this.mediaRecorder.addEventListener('dataavailable', (event) => {
      audioChunks.push(event.data);
    });

    this.mediaRecorder.addEventListener('stop', () => {
      console.log('stop');
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    });
  }

  stopRecording(): void {
    this.isRecording = false;
    this.mediaRecorder.stop();
  }

  processAudioRecording(blob: Blob) {
    // this.url = URL.createObjectURL(blob);
    // console.log('blob', blob);
    // console.log('url', this.url);
  }
}
