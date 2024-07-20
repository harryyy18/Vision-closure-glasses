// static/scripts.js
document.getElementById('start-detection').addEventListener('click', function() {
    const videoFeed = document.getElementById('video-feed');
    videoFeed.src = "/video_feed";
    videoFeed.style.display = "block";
    document.getElementById('start-detection').style.display = "none";
    document.getElementById('stop-detection').style.display = "inline-block";
});

document.getElementById('stop-detection').addEventListener('click', function() {
    const videoFeed = document.getElementById('video-feed');
    videoFeed.src = "#";
    videoFeed.style.display = "none";
    document.getElementById('start-detection').style.display = "inline-block";
    document.getElementById('stop-detection').style.display = "none";
});
