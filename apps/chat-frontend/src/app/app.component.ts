import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';

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
    // Important: unmute the audio element on user interaction to allow autoplay on mobile devices
    this.audioPlayer.nativeElement.muted = false;

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
            const blob = new Blob(chunks, { type: 'audio/mpeg' });
            this.audioPlayer.nativeElement.src = URL.createObjectURL(blob);
            const tracks = stream.getTracks();
            tracks.forEach((track) => track.stop());

            const promise = this.audioPlayer.nativeElement.play();
            if (promise !== undefined) {
              promise
                .catch((error) => {
                  // Auto-play was prevented
                  // Show a UI element to let the user manually start playback
                  console.error(error);
                  console.error('Auto-play was prevented');
                })
                .then(() => {
                  // Auto-play started
                });
            }
          };

          this.recorder.start();
        })
        .catch((error) => {
          console.error(`An error occurred: ${error}`);
        });
    }
  }

  @HostListener('window:keydown', ['$event'])
  onKeyPress($event: KeyboardEvent): void {
    if (
      $event.key === ' ' ||
      $event.code === 'Space' ||
      $event.keyCode === 32
    ) {
      $event.preventDefault();
      this.recordAudio();
    }
  }
}
