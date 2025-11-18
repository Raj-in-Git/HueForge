document.getElementById('go').addEventListener('click', async () => {
  const file = document.getElementById('file').files[0];
  if (!file) { alert('choose file'); return; }
  const form = new FormData();
  form.append('file', file);
  form.append('max_dim', document.getElementById('maxdim').value);
  form.append('scale_xy', document.getElementById('scalexy').value);
  form.append('z_scale', document.getElementById('zscale').value);
  form.append('base_thickness', document.getElementById('base').value);

  const res = await fetch('/generate', { method: 'POST', body: form });
  if (!res.ok) { alert('error'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'hueforge_model.stl';
  a.textContent = 'Download STL';
  document.getElementById('result').innerHTML = '';
  document.getElementById('result').appendChild(a);
});
