// AI Radio Station PWA Frontend (Phase 0)
document.addEventListener('DOMContentLoaded', async () => {
  const grid = document.getElementById('channelGrid');

  try {
    const res = await fetch('./api/channels.php');
    const channels = await res.json();

    grid.innerHTML = channels.map(ch => `
      <div class="channel-card" onclick="location.href='player.html?id=${ch.id}'">
        <h3>${escapeHtml(ch.name)}</h3>
        <p>${escapeHtml(ch.description)}</p>
      </div>
    `).join('');
  } catch (e) {
    grid.innerHTML = '<p>チャンネルを読み込めませんでした。</p>';
  }
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
