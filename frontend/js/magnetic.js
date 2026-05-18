/**
 * Magnetic Button Interaction
 * Applies a "pull" and slight tilt effect when the cursor is near .btn elements.
 */

document.addEventListener('DOMContentLoaded', () => {
    initMagneticButtons();
});

function initMagneticButtons() {
    const buttons = document.querySelectorAll('.btn-primary');
    
    buttons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            
            // Calculate center of button
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            // Calculate distance from center to mouse
            const distanceX = e.clientX - centerX;
            const distanceY = e.clientY - centerY;
            
            // Magnetic pull (max 10px translate)
            const pullX = distanceX * 0.3;
            const pullY = distanceY * 0.3;
            
            // Set dynamic CSS variables for metallic sheen
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            btn.style.setProperty('--mouse-x', `${x}%`);
            btn.style.setProperty('--mouse-y', `${y}%`);
            
            btn.style.transform = `translate(${pullX}px, ${pullY}px) scale(1.02)`;
        });
        
        btn.addEventListener('mouseleave', () => {
            // Reset to original position smoothly
            btn.style.transform = 'translate(0px, 0px) scale(1)';
            btn.style.setProperty('--mouse-x', `50%`);
            btn.style.setProperty('--mouse-y', `50%`);
        });
    });
}
