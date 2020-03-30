var globalStore = new Vue({
  data: {
    playlist_id: '',
    paused: true
  }
})

// A local component as an object
TrackItem = {
  props: {
    track: Object
  },
  methods: {
    playTrack: function() {
      var url = 'https://api.spotify.com/v1/me/player/play'
      var track_id = this.track.id;

      $.ajax(url, {
        method: 'PUT',
        headers: {Authorization: 'Bearer ' + access_token},
        data: JSON.stringify({
          context_uri: 'spotify:user:spotify:playlist:' + globalStore.playlist_id,
          offset: {position: track_id}
        })
      })
    }
  },
  template: `
    <div class="track-item" v-on:click="playTrack">{{ track.name }}</div>
  `
}

SublistManager = {
  template: `
    <b-modal id="manage-sublists-modal" scrollable header-bg-variant="dark" body-bg-variant="dark" footer-bg-variant="dark" title="Add a sublist" @ok="addSublist(selected_sublist)">
      <b-form-group label="Individual radios">
        <div id="sublist-list">
          <b-form-radio v-model="selected_sublist" name="some-radios" v-bind:value="playlist.playlist_id"
            v-for="playlist in playlists"
            v-bind:key="playlist.id"
          >{{ playlist.name }}</b-form-radio>
        </div>
      </b-form-group>
    </b-modal>
  `,
  data: function() {
    return {
      playlists: []
    }
  },
  computed: {
    playlist_id: function() {
      return globalStore.playlist_id;
    }
  },
  methods: {
    refresh: function() {
      this.playlists = [];
      this.fetchList('https://api.spotify.com/v1/me/playlists');
    },
    fetchList: function(url) {
      $.ajax(url, {
        dataType: 'json',
        headers: {Authorization: 'Bearer ' + access_token},
        data: {limit: 50}
      })
      .then((data) => {
        for (playlist of data.items) {
          var playlist_obj = {
            id: this.playlists.length,
            name: playlist.name,
            playlist_id: playlist.id
          };

          if (playlist_obj.id !== this.playlist_id) {
            this.playlists.push(playlist_obj);
          }
        }

        var next_url = data.next;

        if (next_url) {
          this.fetchList(next_url);
        }
      })
    },
    addSublist: function(sublist_id) {
      var url = 'http://127.0.0.1:8000/spotivore/api/playlists/' + this.playlist_id + '/sublists';

      $.ajax(url, {
        method: 'POST',
        dataType: 'json',
        data: {sublist_id: sublist_id}
      })
      .done(() => {
        console.log('success');
      })
      .fail(() => {
        console.log('failure');
      })
    }
  },
  created: function() {
    this.refresh();
  },
}

Vue.component('track-list', {
  data: function() {
    return {
      'tracks': []
    }
  },
  components: {
    'track-item': TrackItem,
    'sublist-manager': SublistManager
  },
  template: `
    <div>
      <div id="track-list-header">
        <h3>Tracks</h3>
        <span id="playlist-tools">
          <b-button id="sync-playlist-btn" class="fas fa-sync-alt" v-on:click="refresh" title="Sync playlist with Spotify"></b-button>
          <b-button id="manage-sublists-btn" class="far fa-list-alt" v-b-modal.manage-sublists-modal title="Manage sublists"></b-button>
          <b-button id="pull-from-sublists-btn" class="fas fa-share-square" title="Pull tracks from sublists"></b-button>
          <b-button id="save-playlist-btn" class="fas fa-save" title="Save playlist to Spotify"></b-button>
        </span>
      </div>
      <track-item
        v-for="item in tracks"
        v-bind:track="item"
        v-bind:key="item.id"
      ></track-item>
      <sublist-manager/>
    </div>
  `,
  computed: {
    playlist_id: function() {
      return globalStore.playlist_id;
    }
  },
  watch: {
    playlist_id: function() {
      this.refresh();
    },
  },
  methods: {
    refresh: function() {
      this.tracks = [];
      var url = 'https://api.spotify.com/v1/playlists/' + this.playlist_id + '/tracks';
      this.fetchList(url);
    },
    fetchList: function(url) {
      $.ajax(url, {
        headers: {Authorization: 'Bearer ' + access_token},
      })
      .then((data) => {
        for (playlist_track of data.items) {
          var track = playlist_track.track

          var track_obj = {
            id: this.tracks.length,
            name: track.name,
            track_id: track.id
          };

          this.tracks.push(track_obj);
        }

        var next_url = data.next;

        if (next_url) {
          this.fetchList(next_url);
        }
      })
    }
  }
})

PlaylistItem = {
  props: {
    playlist: Object,
  },
  methods: {
    setPlaylist: function() {
      globalStore.playlist_id = this.playlist.playlist_id;
    }
  },
  computed: {
    selected: function() {
      return globalStore.playlist_id === this.playlist.playlist_id;
    }
  },
  template: `
    <div class="playlist-item" v-bind:class="{active: selected}" v-bind:title="playlist.name" v-on:click="setPlaylist">
      <div class="playlist-item-text sidebar-left-item">{{ playlist.name }}</div>
    </div>
  `
}

Vue.component('playlist-list', {
  data: function() {
    return {
      playlists: []
    }
  },
  components: {
    'playlist-item': PlaylistItem
  },
  template: `
    <div id="playlist-list">
      <div class="header-caps sidebar-left-item" v-on:click="refresh">PLAYLISTS</div>
      <playlist-item
        v-for="item in playlists"
        v-bind:playlist="item"
        v-bind:key="item.id"
      ></playlist-item>
    </div>
  `,
  methods: {
    refresh: function() {
      this.playlists = [];
      this.fetchList('https://api.spotify.com/v1/me/playlists');
    },
    fetchList: function(url) {
      $.ajax(url, {
        dataType: 'json',
        headers: {Authorization: 'Bearer ' + access_token},
        data: {limit: 50}
      })
      .then((data) => {
        for (playlist of data.items) {
          var playlist_obj = {
            id: this.playlists.length,
            name: playlist.name,
            playlist_id: playlist.id
          };

          this.playlists.push(playlist_obj);
        }

        var next_url = data.next;

        if (next_url) {
          this.fetchList(next_url);
        }
      })
    }
  },
  created: function() {
    this.refresh();
  }
})

PlayerComponent = {
  computed: {
    paused: function() {
      return globalStore.paused;
    }
  },
  template: `
    <div id="player-wrapper">
        <div id="song-info"></div>
        <div id="player-controls">
          <div id="play-button-wrapper">
            <div id="play-button">
              <i class="fas" v-bind:class="[paused ? 'fa-play' : 'fa-pause']" onclick="player.togglePlay()"></i>
            </div>
          </div>
          <div id="scrubber-wrapper">
            <div id="scrubber-line"></div>
          </div>
        </div>
        <div id="volume-control"></div>
    </div>
  `
}

var app = new Vue({
  el: '#app',
  data: {
    currPlaylist: ''
  },
  components: {
    'player-component': PlayerComponent
  },
  template: `
    <b-container fluid>
      <b-row id="main-row">
        <b-col id="sidebar-left" class="sidebar">
          <playlist-list></playlist-list>
        </b-col>
        <b-col id="main-content">
          <track-list></track-list>
        </b-col>
        <b-col id="sidebar-right" class="sidebar"></b-col>
      </b-row>
      <b-row id="player-row">
        <player-component></player-component>
      </b-row>
    </b-container>
  `
})