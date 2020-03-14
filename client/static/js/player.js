var template_data = JSON.parse($('#template-data').text())
var access_token = template_data['access_token']
var expires_in = template_data['expires_in']

/*function setRefreshTimer(expires_in) {
  // Duration (in milliseconds) of the timer
  // We'll refresh the token shortly before it expires
  var duration = (expires_in - 120) * 1000;

  setTimeout(function() {
    var url = '';

    $getJSON()
  }, duration);
}*/

$(function() {
  window.onSpotifyWebPlaybackSDKReady = () => {
    player = new Spotify.Player({
      name: 'Web Playback SDK Quick Start Player',
      getOAuthToken: cb => { cb(access_token); }
    });

    // Error handling
    player.addListener('initialization_error', ({ message }) => { console.error(message); });
    player.addListener('authentication_error', ({ message }) => { console.error(message); });
    player.addListener('account_error', ({ message }) => { console.error(message); });
    player.addListener('playback_error', ({ message }) => { console.error(message); });

    // Playback status updates
    player.addListener('player_state_changed', state => {
      globalStore.paused = state.paused;
    });

    // Ready
    player.addListener('ready', ({ device_id }) => {
      console.log('Ready with Device ID', device_id);
      $('#play-button').prop('disabled', false);
    });

    // Not Ready
    player.addListener('not_ready', ({ device_id }) => {
      console.log('Device ID has gone offline', device_id);
      $('#play-button').prop('disabled', true);
    });

    // Connect to the player!
    player.connect();
  };
});
