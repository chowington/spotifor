var player;

$(function() {
  window.onSpotifyWebPlaybackSDKReady = () => {
    const token = 'BQAw5-RsXeV27q3uKCFgJJxpDXY42LEdjac8aZzpJgTne9VyYBZKzOe-jaehU0Q0rTIqD8L7gRjhvP-t767z-_DeT_TduKdKr0f3ZwYQXUb94kfWQeaf2_FL8o5t_rTruq8c75O5bvt05aWYy8063wcSd7JrktgK2Ab38iIbFkE2jVvEpxAqOF-aKmdZ';
    player = new Spotify.Player({
      name: 'Web Playback SDK Quick Start Player',
      getOAuthToken: cb => { cb(token); }
    });

    // Error handling
    player.addListener('initialization_error', ({ message }) => { console.error(message); });
    player.addListener('authentication_error', ({ message }) => { console.error(message); });
    player.addListener('account_error', ({ message }) => { console.error(message); });
    player.addListener('playback_error', ({ message }) => { console.error(message); });

    // Playback status updates
    player.addListener('player_state_changed', state => {
      app.paused = state.paused;
    });

    // Ready
    player.addListener('ready', ({ device_id }) => {
      console.log('Ready with Device ID', device_id);
      $('#status').text('Connected!');
      $('#play-button').prop('disabled', false);
    });

    // Not Ready
    player.addListener('not_ready', ({ device_id }) => {
      console.log('Device ID has gone offline', device_id);
      $('#status').text('Not connected.');
      $('#play-button').prop('disabled', true);
    });

    // Connect to the player!
    player.connect();
  };
});

function togglePlay() {
  player.togglePlay();
};
