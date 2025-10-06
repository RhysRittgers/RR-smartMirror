(function(){
  const surface = document.getElementById('surface');
  if (!surface) return;

  let dragging = null;

  function posToGrid(clientX, clientY){
    const rect = surface.getBoundingClientRect();
    const xRatio = (clientX - rect.left) / rect.width;
    const col = Math.max(0, Math.min(11, Math.floor(xRatio * 12)));
    const row = Math.max(0, Math.floor((clientY - rect.top) / 90)); // 90px rows
    return {x: col, y: row};
  }

  surface.querySelectorAll('.tile').forEach(tile => {
    tile.style.cursor = 'move';
    tile.addEventListener('pointerdown', (e) => {
      dragging = tile;
      tile.setPointerCapture(e.pointerId);
    });
    tile.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      const {x, y} = posToGrid(e.clientX, e.clientY);
      const colStr = tile.style.gridColumn || "1 / span 1";
      const rowStr = tile.style.gridRow || "1 / span 1";
      const w = parseInt((colStr.split('span ')[1] || '1').trim());
      const h = parseInt((rowStr.split('span ')[1] || '1').trim());
      tile.style.gridColumn = (x+1) + " / span " + w;
      tile.style.gridRow = (y+1) + " / span " + h;
    });
    tile.addEventListener('pointerup', async (e) => {
      if (!dragging) return;
      const id = tile.getAttribute('data-id');
      const colStr = tile.style.gridColumn || "1 / span 1";
      const rowStr = tile.style.gridRow || "1 / span 1";
      const x = parseInt(colStr.split('/')[0]) - 1;
      const w = parseInt((colStr.split('span ')[1] || '1').trim());
      const y = parseInt(rowStr.split('/')[0]) - 1;
      const h = parseInt((rowStr.split('span ')[1] || '1').trim());
      dragging = null;
      try {
        await fetch('/modules/layout/update/', {
          method: 'POST',
          headers: {'Content-Type':'application/json', 'X-CSRFToken': getCookie('csrftoken')},
          credentials: 'include',
          body: JSON.stringify([{id: Number(id), x, y, w, h}]),
        });
      } catch (e) {
        console.error('layout update failed', e);
      }
    });
  });

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
})();
