import { HttpClient } from '@angular/common/http';
import {
  Component,
  ElementRef,
  HostListener,
  inject,
  isDevMode,
  ViewChild,
} from '@angular/core';
import { BehaviorSubject, catchError, tap } from 'rxjs';

@Component({
  standalone: true,
  imports: [],
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  #http = inject(HttpClient);

  recorder!: MediaRecorder;
  isRecording = false;
  botStatus = new BehaviorSubject('');

  showAlert = false;
  alertMessage = '';

  @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

  async toggleAudioRecord(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      this.displayAlert(
        "Sorry but it seems that we can't use your microphone."
      );
      return;
    }
    this.hideAlert();

    // Important: unmute the audio element on user interaction to allow autoplay on mobile devices
    this.audioPlayer.nativeElement.muted = false;

    if (this.recorder && this.recorder.state === 'recording') {
      console.log('stop recording');
      this.isRecording = false;
      this.recorder.stop();
      this.setStatus('computing');
    } else {
      console.log('start recording');
      this.isRecording = true;
      this.setStatus('listening');
      await navigator.mediaDevices
        .getUserMedia({
          audio: true,
          video: false,
        })
        .then((stream) => this.processAudioRecording(stream))
        .catch((error) => this.handleError(error));
    }
  }

  processAudioRecording(stream: MediaStream): void {
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
      const tracks = stream.getTracks();
      tracks.forEach((track) => track.stop());

      // Build an audio file and send it to the server
      const audioBlob = new Blob(chunks, { type: 'audio/mpeg' });
      const file = new File([audioBlob], 'record.mpeg', {
        type: 'audio/mpeg',
      });
      const formData = new FormData();
      formData.append('file', file);

      const url = isDevMode() ? `http://localhost:3000/talk` : `/talk`;
      this.#http
        .post(url, formData, {
          responseType: 'blob',
          reportProgress: true,
        })
        .pipe(
          tap((response) => {
            this.setStatus('speaking');
            this.audioPlayer.nativeElement.src = URL.createObjectURL(response);
            const promise = this.audioPlayer.nativeElement.play();

            if (promise !== undefined) {
              promise
                .catch((error) => {
                  // Auto-play was prevented
                  // Show a UI element to let the user manually start playback
                  console.error(error);
                  console.error('Auto-play was prevented');
                  this.displayAlert(
                    error.message || 'Error: Auto-play was prevented'
                  );
                })
                .then(() => {
                  // Auto-play started
                });
            }
          }),
          catchError((error) => {
            console.error('Failed to send audio file to the server', error);
            this.setStatus();
            return [];
          })
        )
        .subscribe();
    };

    this.recorder.start();
  }

  setStatus(newStatus?: string): void {
    if (newStatus) {
      this.botStatus.next(newStatus);
    } else {
      this.botStatus.next('');
    }
  }

  handleError(error: Error): void {
    this.isRecording = false;
    if (error.name?.indexOf('NotAllowedError') !== -1) {
      this.displayAlert(
        'You must allow your browser to use your microphone to use this feature.'
      );
      return;
    }
    this.displayAlert('An error occurred. Please try again.');
  }

  @HostListener('window:keydown', ['$event'])
  onKeyPress($event: KeyboardEvent): void {
    if (
      $event.key === ' ' ||
      $event.code === 'Space' ||
      $event.keyCode === 32
    ) {
      $event.preventDefault();
      this.toggleAudioRecord();
    }
  }

  displayAlert(message: string): void {
    this.showAlert = true;
    this.alertMessage = message;
  }

  hideAlert(): void {
    this.showAlert = false;
  }
}
