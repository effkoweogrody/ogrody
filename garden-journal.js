/* Keep each garden story readable at a glance, with its complete text on demand. */
document.querySelectorAll('[data-garden-story]').forEach(button => {
  const dialog = document.getElementById(button.dataset.gardenStory);
  if (!dialog) return;
  button.addEventListener('click', () => {
    document.documentElement.classList.add('garden-story-is-open');
    window.syncOverlayScrollLock?.();
    dialog.showModal();
    dialog.scrollTop = 0;
  });
  dialog.querySelector('.garden-story-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.documentElement.classList.remove('garden-story-is-open');
    window.syncOverlayScrollLock?.();
    button.focus({ preventScroll: true });
  });
});
