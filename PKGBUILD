# Maintainer: Bravin Evans Kiplagat <bravinevans1@gmail.com>
pkgname=ytgrab
pkgver=0.4.0
pkgrel=1
pkgdesc="Minimalist PyQt6 GUI for yt-dlp with automatic RD Mix URL resolution and anti-403 pacing"
arch=('any')
url="https://github.com/bravinevans/ytgrab"
license=('MIT')
depends=('python' 'python-pyqt6' 'yt-dlp' 'ffmpeg')
optdepends=('python-mutagen: enhanced metadata and thumbnail embedding')
source=("ytgrab.py"
        "ytgrab.desktop"
        "ytgrab.svg")
sha256sums=('SKIP'
            'SKIP'
            'SKIP')

package() {
    install -Dm755 "${srcdir}/ytgrab.py" "${pkgdir}/usr/bin/ytgrab"
    install -Dm644 "${srcdir}/ytgrab.desktop" "${pkgdir}/usr/share/applications/ytgrab.desktop"
    install -Dm644 "${srcdir}/ytgrab.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/ytgrab.svg"
}
