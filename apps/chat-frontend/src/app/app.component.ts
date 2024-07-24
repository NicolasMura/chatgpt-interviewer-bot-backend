import { Component, ElementRef, ViewChild } from '@angular/core';

@Component({
  standalone: true,
  imports: [],
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  recorder!: MediaRecorder;
  isRecording = false;

  @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

  async recordAudio(): Promise<void> {
    if (this.recorder && this.recorder.state === 'recording') {
      console.log('stop recording');
      this.isRecording = false;
      this.recorder.stop();
    } else {
      console.log('start recording');
      this.isRecording = true;
      await navigator.mediaDevices
        .getUserMedia({
          audio: true,
          video: false,
        })
        .then((stream) => {
          this.recorder = new MediaRecorder(stream);

          const chunks: Blob[] = [];
          this.recorder.ondataavailable = (event) => {
            if (event.data.size <= 0) {
              return;
            }
            chunks.push(event.data);
          };

          this.recorder.onstart = () => {
            console.log('recording started');
          };

          this.recorder.onstop = () => {
            console.log('recording stopped');
            const blob = new Blob(chunks, { type: 'audio/mp3' });
            this.audioPlayer.nativeElement.src = URL.createObjectURL(blob);
            const tracks = stream.getTracks();
            tracks.forEach((track) => track.stop());
            this.audioPlayer.nativeElement.play();
          };

          this.recorder.start();
        })
        .catch((err) => {
          console.error(`An error occurred: ${err}`);
        });
    }
  }
}
