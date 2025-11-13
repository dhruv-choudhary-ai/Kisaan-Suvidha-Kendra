var pc = null;

function negotiate() {
    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });
    return pc.createOffer().then((offer) => {
        return pc.setLocalDescription(offer);
    }).then(() => {
        // wait for ICE gathering to complete
        return new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        var offer = pc.localDescription;
        console.log('📤 Sending WebRTC offer to /offer endpoint...');
        console.log('Offer SDP length:', offer.sdp.length);
        
        // Add timeout to fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            console.error('❌ Request timeout after 10 seconds');
        }, 10000);
        
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST',
            signal: controller.signal
        }).then(response => {
            clearTimeout(timeoutId);
            return response;
        });
    }).then((response) => {
        console.log('📥 Received response from server:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
    }).then((answer) => {
        console.log('✅ WebRTC answer received, sessionid:', answer.sessionid);
        document.getElementById('sessionid').value = answer.sessionid
        return pc.setRemoteDescription(answer);
    }).catch((e) => {
        console.error('❌ WebRTC negotiation failed:', e);
        console.error('Error details:', e.message);
        console.error('Stack trace:', e.stack);

        // More detailed error messages
        let errorMessage = 'Connection failed: ' + e.message;
        if (e.message.includes('500')) {
            errorMessage = 'Server error: The backend returned an internal error. Check if avatar files and models are properly configured.';
        } else if (e.message.includes('404')) {
            errorMessage = 'Endpoint not found: The /offer endpoint is not available on the server.';
        } else if (e.message.includes('CORS')) {
            errorMessage = 'CORS error: Cross-origin request blocked. Check server CORS configuration.';
        }

        alert(errorMessage);

        // Dispatch custom event for React to handle
        window.dispatchEvent(new CustomEvent('webrtc-error', {
            detail: { error: e, message: errorMessage }
        }));
    });
}

function start() {
    console.log('🚀 Starting WebRTC connection...');
    
    var config = {
        sdpSemantics: 'unified-plan'
    };

    if (document.getElementById('use-stun').checked) {
        config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }];
    }

    pc = new RTCPeerConnection(config);
    console.log('📡 RTCPeerConnection created');

    // connect audio / video
    pc.addEventListener('track', (evt) => {
        console.log('🎬 Received track:', evt.track.kind, 'enabled:', evt.track.enabled, 'readyState:', evt.track.readyState);
        if (evt.track.kind == 'video') {
            const videoElement = document.getElementById('avatar-video');
            if (videoElement) {
                videoElement.srcObject = evt.streams[0];
                console.log('✅ Video stream attached to element');
                console.log('Video element dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
            } else {
                console.error('❌ Video element not found in DOM!');
            }
        } else {
            // Attach audio to the same video element (video elements can handle both video and audio)
            const videoElement = document.getElementById('avatar-video');
            if (videoElement) {
                // Audio track will be automatically handled by the video element
                console.log('✅ Audio track received - will be handled by video element');
            } else {
                console.error('❌ Video element not found for audio track!');
            }
        }
    });

    // Add connection state monitoring
    pc.addEventListener('connectionstatechange', () => {
        console.log('🔗 WebRTC connection state:', pc.connectionState);
        if (pc.connectionState === 'failed') {
            console.error('❌ WebRTC connection failed');
            window.dispatchEvent(new CustomEvent('webrtc-connection-failed'));
        } else if (pc.connectionState === 'connected') {
            console.log('✅ WebRTC connection established');
            window.dispatchEvent(new CustomEvent('webrtc-connected'));
        }
    });

    const startBtn = document.getElementById('start');
    const stopBtn = document.getElementById('stop');
    
    if (startBtn) startBtn.style.display = 'none';
    
    negotiate();
    
    if (stopBtn) stopBtn.style.display = 'inline-block';
}

function stop() {
    console.log('🛑 Stopping WebRTC connection...');
    
    const stopBtn = document.getElementById('stop');
    if (stopBtn) stopBtn.style.display = 'none';

    // close peer connection
    setTimeout(() => {
        if (pc) {
            pc.close();
            console.log('✅ Connection closed');
        }
    }, 500);
}

window.onunload = function(event) {
    // Execute the operation you want here
    setTimeout(() => {
        if (pc) pc.close();
    }, 500);
};

window.onbeforeunload = function (e) {
    setTimeout(() => {
        if (pc) pc.close();
    }, 500);
    e = e || window.event
    // Compatible with IE8 and Firefox 4 and earlier versions
    if (e) {
      e.returnValue = 'Close prompt'
    }
    // Chrome, Safari, Firefox 4+, Opera 12+ , IE 9+
    return 'Close prompt'
}

// Test backend connectivity
function testBackendConnection() {
    console.log('🔍 Testing backend connectivity...');

    // Test basic endpoint
    fetch('/').then(response => {
        console.log('📡 Basic endpoint response:', response.status);
        return response.text();
    }).then(text => {
        console.log('📄 Basic endpoint content preview:', text.substring(0, 200));
    }).catch(error => {
        console.error('❌ Basic endpoint failed:', error);
    });

    // Test offer endpoint with minimal payload
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    fetch('/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test: true }),
        signal: controller.signal
    }).then(response => {
        clearTimeout(timeoutId);
        console.log('📤 Offer endpoint response:', response.status, response.statusText);
        return response.text();
    }).then(text => {
        console.log('📄 Offer endpoint response:', text);
    }).catch(error => {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            console.error('❌ Offer endpoint timeout after 5 seconds');
        } else {
            console.error('❌ Offer endpoint failed:', error);
        }
    });

    // Test direct connection to backend (bypass proxy)
    fetch('https://jltzsxc1c8xlp3-8010.proxy.runpod.net/', {
        mode: 'cors'
    }).then(response => {
        console.log('🔗 Direct backend connection:', response.status);
        return response.text();
    }).then(text => {
        console.log('📄 Direct backend response:', text.substring(0, 200));
    }).catch(error => {
        console.error('❌ Direct backend connection failed:', error);
    });
}

// Expose functions globally
window.startWebRTC = start;
window.stopWebRTC = stop;
window.testBackendConnection = testBackendConnection;
