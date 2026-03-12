let wavesurfer, wsRegions;
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const editorContainer = document.getElementById('editor-container');
const btnPlayPause = document.getElementById('btn-play-pause');
const btnStop = document.getElementById('btn-stop');
const btnTrim = document.getElementById('btn-trim');
const btnDownload = document.getElementById('btn-download');
const fileNameDisplay = document.getElementById('file-name');
const selectionRangeDisplay = document.getElementById('selection-range');

// Initialize Wavesurfer
const initWaveSurfer = () => {
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#4f46e5',
        progressColor: '#6366f1',
        cursorColor: '#ec4899',
        barWidth: 2,
        barRadius: 3,
        responsive: true,
        height: 120,
        normalize: true,
        plugins: []
    });

    // Initialize Regions plugin
    wsRegions = wavesurfer.registerPlugin(WaveSurfer.Regions.create());

    // Event listeners for Wavesurfer
    wavesurfer.on('interaction', () => wavesurfer.play());
    
    wsRegions.on('region-updated', (region) => {
        const start = region.start.toFixed(2);
        const end = region.end.toFixed(2);
        selectionRangeDisplay.textContent = `${start}s - ${end}s`;
    });

    wsRegions.on('region-created', (region) => {
        // Only allow one region at a time
        wsRegions.getRegions().forEach(r => {
            if (r !== region) r.remove();
        });
    });
};

// Handle File upload
const handleFile = (file) => {
    if (!file || !file.type.startsWith('audio/')) {
        alert('올바른 사운드 파일을 선택해주세요.');
        return;
    }

    fileNameDisplay.textContent = file.name;
    const reader = new FileReader();
    reader.onload = (e) => {
        if (!wavesurfer) initWaveSurfer();
        wavesurfer.load(e.target.result);
        
        // Setup initial region after loading
        wavesurfer.once('ready', () => {
            const duration = wavesurfer.getDuration();
            wsRegions.addRegion({
                start: duration * 0.1,
                end: duration * 0.9,
                color: 'rgba(99, 102, 241, 0.2)',
                drag: true,
                resize: true
            });
            editorContainer.classList.remove('hidden');
            dropZone.classList.add('hidden');
        });
    };
    reader.readAsDataURL(file);
};

// Playback Controls
btnPlayPause.addEventListener('click', () => {
    wavesurfer.playPause();
    const isPlaying = wavesurfer.isPlaying();
    btnPlayPause.querySelector('span').className = isPlaying ? 'icon-pause' : 'icon-play';
});

btnStop.addEventListener('click', () => {
    wavesurfer.stop();
    btnPlayPause.querySelector('span').className = 'icon-play';
});

// Trimming Logic (Web Audio API)
const trimAudio = async () => {
    const region = wsRegions.getRegions()[0];
    if (!region) return;

    const start = region.start;
    const end = region.end;
    const duration = end - start;

    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const response = await fetch(wavesurfer.getSrc());
    const arrayBuffer = await response.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    const sampleRate = audioBuffer.sampleRate;
    const frameCount = Math.floor(duration * sampleRate);
    const trimmedBuffer = audioContext.createBuffer(
        audioBuffer.numberOfChannels,
        frameCount,
        sampleRate
    );

    for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
        const channelData = audioBuffer.getChannelData(i);
        const trimmedData = trimmedBuffer.getChannelData(i);
        const startOffset = Math.floor(start * sampleRate);
        
        for (let j = 0; j < frameCount; j++) {
            trimmedData[j] = channelData[startOffset + j];
        }
    }

    return trimmedBuffer;
};

// Export to WAV
const bufferToWav = (buffer) => {
    const numOfChan = buffer.numberOfChannels,
        length = buffer.length * numOfChan * 2 + 44,
        buffer_wav = new ArrayBuffer(length),
        view = new DataView(buffer_wav),
        channels = [],
        sampleRate = buffer.sampleRate;
    let i, sample, offset = 0, pos = 0;

    // WAV Header
    setUint32(0x46464952); // "RIFF"
    setUint32(length - 8);  // file length - 8
    setUint32(0x45564157); // "WAVE"
    setUint32(0x20746d66); // "fmt "
    setUint32(16);         // length of fmt chunk
    setUint16(1);          // PCM format
    setUint16(numOfChan);
    setUint32(sampleRate);
    setUint32(sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2);
    setUint16(16);         // bits per sample
    setUint32(0x61746164); // "data"
    setUint32(buffer.length * numOfChan * 2); // data chunk length

    for (i = 0; i < numOfChan; i++) channels.push(buffer.getChannelData(i));

    while (pos < buffer.length) {
        for (i = 0; i < numOfChan; i++) {
            sample = Math.max(-1, Math.min(1, channels[i][pos]));
            sample = (sample < 0 ? sample * 0x8000 : sample * 0x7FFF);
            view.setInt16(offset, sample, true);
            offset += 2;
        }
        pos++;
    }

    return new Blob([buffer_wav], { type: "audio/wav" });

    function setUint16(data) { view.setUint16(offset, data, true); offset += 2; }
    function setUint32(data) { view.setUint32(offset, data, true); offset += 4; }
};

btnTrim.addEventListener('click', async () => {
    const region = wsRegions.getRegions()[0];
    if (!region) {
        alert('잘라낼 구간을 선택해주세요.');
        return;
    }

    try {
        btnTrim.disabled = true;
        btnTrim.textContent = '처리 중...';
        
        const trimmedBuffer = await trimAudio();
        if (trimmedBuffer) {
            const wavBlob = bufferToWav(trimmedBuffer);
            const url = URL.createObjectURL(wavBlob);
            wavesurfer.load(url);
            
            // Re-initialize regions after load
            wavesurfer.once('ready', () => {
                wsRegions.clearRegions();
                const duration = wavesurfer.getDuration();
                wsRegions.addRegion({
                    start: duration * 0.1,
                    end: duration * 0.9,
                    color: 'rgba(99, 102, 241, 0.2)',
                    drag: true,
                    resize: true
                });
                btnTrim.disabled = false;
                btnTrim.textContent = '선택 영역 잘라내기';
                alert('선택한 구간으로 잘라내었습니다.');
            });
        }
    } catch (err) {
        console.error('Trim failed:', err);
        alert('잘라내기 중 오류가 발생했습니다: ' + err.message);
        btnTrim.disabled = false;
        btnTrim.textContent = '선택 영역 잘라내기';
    }
});

btnDownload.addEventListener('click', async () => {
    const currentSrc = wavesurfer.getSrc();
    if (!currentSrc) {
        alert('편집할 파일이 없습니다.');
        return;
    }
    
    try {
        btnDownload.disabled = true;
        btnDownload.textContent = '준비 중...';

        const response = await fetch(currentSrc);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.style.display = 'none';
        link.href = url;
        
        // Robust filename logic
        let baseName = fileNameDisplay.textContent.trim();
        if (!baseName || baseName === '-') baseName = 'edited_audio';
        if (baseName.includes('.')) {
            baseName = baseName.substring(0, baseName.lastIndexOf('.'));
        }
        
        link.setAttribute('download', `${baseName}_edited.wav`);
        
        document.body.appendChild(link);
        link.click();
        
        setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            btnDownload.disabled = false;
            btnDownload.textContent = '내보내기 (Export)';
        }, 100);
        
    } catch (err) {
        console.error('Download failed:', err);
        alert('다운로드 중 오류가 발생했습니다: ' + err.message);
        btnDownload.disabled = false;
        btnDownload.textContent = '내보내기 (Export)';
    }
});

// Event Listeners for UI
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--primary-color)';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--glass-border)';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
    handleFile(e.target.files[0]);
});
