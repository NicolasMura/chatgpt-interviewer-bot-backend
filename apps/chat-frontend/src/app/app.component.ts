import { AsyncPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  Component,
  ElementRef,
  HostListener,
  inject,
  isDevMode,
  OnInit,
  ViewChild,
} from '@angular/core';
import { BehaviorSubject, catchError, tap } from 'rxjs';

@Component({
  standalone: true,
  imports: [AsyncPipe],
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit {
  #http = inject(HttpClient);

  selectedAudioInputDevice?: MediaDeviceInfo;
  recorder!: MediaRecorder;
  isRecording = false;
  micDisabled = false;
  isBotComputingOrSpeaking = false;
  botStatusSubject = new BehaviorSubject('');

  showAlert = new BehaviorSubject(false);
  alertMessage = '';
  isAlertInfo = false;

  @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

  microphonePermission!: PermissionStatus;

  async ngOnInit(): Promise<void> {
    await navigator.mediaDevices
      ?.enumerateDevices()
      .then((devices) => {
        console.log('Detected devices:');
        console.log(devices);
        // Pick the default audio input device
        this.selectedAudioInputDevice =
          devices?.find((device) => device.kind === 'audioinput') || undefined;
        console.log('selectedAudioInputDevice :');
        console.log(this.selectedAudioInputDevice);
      })
      .catch((error) => this.handleError(error));

    if (!this.selectedAudioInputDevice) {
      this.micDisabled = true;
      this.displayAlert(
        'No microphone detected. Please check your microphone is correctly plugged in and working.'
      );
      return;
    }

    this.microphonePermission = await this.getMicrophonePermission();

    if (this.microphonePermission?.state === 'granted') {
      // OK - Access has been granted to the microphone
      console.log('OK - Access has been granted to the microphone');
    } else if (this.microphonePermission?.state === 'denied') {
      // KO - Access has been denied. Microphone can't be used
      console.log("KO - Access has been denied. Microphone can't be used");
      // Voir https://www.viamichelin.fr pour un cas concret de re-demande de permission
    } else {
      // Permission should be asked
      console.log('Permission should be asked');
    }

    this.listenForMicrophonePermissionChanges(this.microphonePermission);
  }

  async getMicrophonePermission(): Promise<PermissionStatus> {
    return await navigator.permissions.query({
      name: 'microphone' as any, // TypeScript doesn't know about the 'microphone' permission yet
    });
  }

  listenForMicrophonePermissionChanges(
    microphonePermission: PermissionStatus
  ): void {
    microphonePermission.onchange = (event) => {
      // React when the permission changed
      if ((event.currentTarget as PermissionStatus)?.state === 'denied') {
        // OK - Access has been granted to the microphone
        console.log("KO - Access has been denied. Microphone can't be used");
        this.displayAlert(
          'You must allow your browser to use your microphone to use this feature.'
        );
      }
      if ((event.currentTarget as PermissionStatus)?.state === 'granted') {
        // OK - Access has been granted to the microphone
        console.log('OK - Access has been granted to the microphone');
        this.hideAlert();
      }
    };
  }

  async toggleAudioRecord(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      this.displayAlert(
        "Sorry but it seems that we can't use your microphone."
      );
      return;
    }
    this.hideAlert();

    if (!this.selectedAudioInputDevice) {
      this.displayAlert(
        'No microphone detected. Please check your microphone is correctly plugged in and working.'
      );
      return;
    }

    if (this.micDisabled) {
      return;
    }

    // @TODO check if this block is useful and if yes how to do better :)
    if ((window as any).stream) {
      console.log('stop all tracks');
      (window as any).stream.getTracks().forEach((track: any) => {
        track.stop();
      });
    }

    // Important: unmute the audio element on user interaction to allow autoplay on mobile devices
    this.audioPlayer.nativeElement.muted = false;

    if (this.recorder && this.recorder.state === 'recording') {
      console.log('stop recording');
      this.isRecording = false;
      this.recorder.stop();
      this.setBotStatus('computing');
    } else {
      if (this.isBotComputingOrSpeaking) return;

      console.log('navigator.mediaDevices.getUserMedia');
      await navigator.mediaDevices
        .getUserMedia({
          audio: {
            deviceId: this.selectedAudioInputDevice.deviceId,
            autoGainControl: true,
            echoCancellation: true,
            noiseSuppression: true,
          },
          video: false,
        })
        .then((stream) => this.processAudioRecording(stream))
        .catch((error) => this.handleError(error));
    }
  }

  processAudioRecording(stream: MediaStream): void {
    console.log(stream);
    // stream.addTrack(this.selectedAudioInputDevice);
    console.log('start recording');
    this.isRecording = true;
    this.setBotStatus('listening');
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
      const audioBlob = new Blob(chunks, { type: 'audio/mp3' }); // Be careful : audio/mpeg not working for iPhone!

      // Build an audio file and send it to the server
      const audioFile = new File([audioBlob], 'record.mp3', {
        type: 'audio/mp3',
      });

      this.sendAudioToServer(audioFile);
    };

    this.recorder.start();
  }

  sendAudioToServer(audioFile: File): void {
    this.isBotComputingOrSpeaking = true;
    const formData = new FormData();
    formData.append('file', audioFile);

    const url = isDevMode() ? 'http://192.168.1.151:3000/talk' : '/talk';
    // const url = 'http://192.168.1.151:3000/talk-fake;' // Useful to bypass backend processing
    this.#http
      .post(url, formData, {
        responseType: 'blob',
      })
      .pipe(
        tap((response) => {
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
                this.setBotStatus();
              })
              .then(() => {
                // Auto-play started
                this.setBotStatus('speaking');
              });
          }

          this.audioPlayer.nativeElement.onended = () => {
            console.log('Audio playback finished');
            this.setBotStatus();
          };
        }),
        catchError((error) => {
          console.error('Failed to send audio file to the server', error);
          this.setBotStatus();
          this.displayAlert(
            'Failed to send audio file to the server, please try again or Failed to send audio file to the server, please try again or <a href="." class="text-blue-600 dark:text-blue-500 hover:underline">reload the app</a>.'
          );
          return [];
        })
      )
      .subscribe();
  }

  setBotStatus(newStatus?: string): void {
    if (newStatus) {
      if (newStatus === 'computing' || newStatus === 'speaking') {
        this.isBotComputingOrSpeaking = true;
      } else {
        this.isBotComputingOrSpeaking = false;
      }
      this.botStatusSubject.next(newStatus);
    } else {
      this.isBotComputingOrSpeaking = false;
      this.botStatusSubject.next('');
    }
  }

  handleError(error: Error, customMessage?: string): void {
    console.error(error);
    this.isRecording = false;
    this.setBotStatus();
    if (error.name?.indexOf('NotAllowedError') !== -1) {
      this.displayAlert(
        'You must allow your browser to use your microphone to use this feature.'
      );
      return;
    }
    if (error.message.indexOf('Could not start audio source') !== -1) {
      this.displayAlert(
        'We could not start audio source. Please check your microphone is correctly plugged in and working.'
      );
      return;
    }

    if (customMessage) {
      this.displayAlert(customMessage);
    } else {
      this.displayAlert('An error occurred. Please try again.');
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
      this.toggleAudioRecord();
    }
  }

  displayAlert(message: string, isInfo = false): void {
    this.showAlert.next(true);
    this.alertMessage = message;
    this.isAlertInfo = isInfo;
  }

  hideAlert(): void {
    this.showAlert.next(false);
  }

  resetChatHistory(): void {
    const url = isDevMode() ? `http://192.168.1.151:3000/reset` : `/reset`;

    this.#http
      .get(url)
      .pipe(
        tap(() => {
          this.displayAlert('Chat history has been reset.', true);
          setTimeout(() => {
            this.hideAlert();
          }, 3000);
        }),
        catchError((error) => {
          this.handleError(
            error,
            'Failed to reset chat history, please try again.'
          );
          return [];
        })
      )
      .subscribe();
  }

  hasTouchScreen(): boolean {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }
}
