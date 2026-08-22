import { renderToStaticMarkup } from 'react-dom/server'
import { createElement } from 'react'
import type { Trip } from '../types/trip'
import TripPage from '../renderers/page/TripPage'
import TripEmail from '../renderers/email/TripEmail'
import TripDocument from '../renderers/document/TripDocument'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function collectInlineCss(): string {
  const cssBlocks: string[] = []
  for (const styleSheet of Array.from(document.styleSheets)) {
    try {
      if (!styleSheet.cssRules) continue
      const css = Array.from(styleSheet.cssRules).map((rule) => rule.cssText).join('\n')
      if (css.trim()) cssBlocks.push(css)
    } catch {
      // Ignore stylesheets that cannot be read because of browser security restrictions.
    }
  }

  return cssBlocks.join('\n')
}

function createHtmlDocument(title: string, markup: string, cssText: string, bodyClass = ''): string {
  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    `  <title>${title}</title>`,
    '  <style>',
    cssText,
    '  </style>',
    '</head>',
    `<body class="${bodyClass}">`,
    markup,
    '</body>',
    '</html>',
  ].join('\n')
}

function downloadTextFile(content: string, fileName: string): void {
  const blob = new Blob([content], { type: 'text/html;charset=utf-8' })
  const blobUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = blobUrl
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(blobUrl)
}

async function waitForPrintAssets(printWindow: Window): Promise<void> {
  const targetDoc = printWindow.document

  if (targetDoc.readyState !== 'complete') {
    await new Promise<void>((resolve) => {
      printWindow.addEventListener('load', () => resolve(), { once: true })
    })
  }

  const imageElements = Array.from(targetDoc.images)
  await Promise.all(
    imageElements.map((image) => {
      if (image.complete) return Promise.resolve()
      return new Promise<void>((resolve) => {
        image.addEventListener('load', () => resolve(), { once: true })
        image.addEventListener('error', () => resolve(), { once: true })
      })
    }),
  )

  if ('fonts' in targetDoc) {
    await targetDoc.fonts.ready.catch(() => undefined)
  }

  await new Promise<void>((resolve) => {
    window.setTimeout(resolve, 120)
  })
}

export function exportTripWebsiteHtml(trip: Trip): void {
  const cssText = collectInlineCss()
  const markup = renderToStaticMarkup(createElement(TripPage, { trip }))
  const title = `Atlas ${trip.destination.name} ${trip.overview.durationDays} Day Guide`
  const html = createHtmlDocument(title, markup, cssText)
  const exportBaseName = `${slugify(trip.destination.name)}-${trip.overview.durationDays}-days`
  downloadTextFile(html, `atlas-${exportBaseName}.html`)
}

export function exportTripEmailHtml(trip: Trip): void {
  const cssText = collectInlineCss()
  const markup = renderToStaticMarkup(createElement(TripEmail, { trip }))
  const title = `Atlas Email ${trip.destination.name}`
  const html = createHtmlDocument(title, markup, cssText)
  downloadTextFile(html, `atlas-email-${slugify(trip.destination.name)}.html`)
}

export function exportTripGuidePdf(trip: Trip): void {
  const cssText = collectInlineCss()
  const markup = renderToStaticMarkup(createElement(TripDocument, { trip }))
  if (!markup.trim()) {
    throw new Error('Travel Guide render produced empty markup.')
  }

  const title = `Atlas Travel Guide ${trip.destination.name}`
  const printCss = `${cssText}\n@page { size: A4; margin: 12mm; }\nhtml, body { margin: 0; padding: 0; background: #ffffff; }`
  const printHtml = createHtmlDocument(title, markup, printCss)
  const printWindow = window.open('', '_blank', 'width=1200,height=900')
  if (!printWindow) return

  printWindow.document.open()
  printWindow.document.write(printHtml)
  printWindow.document.close()

  void waitForPrintAssets(printWindow).then(() => {
    printWindow.focus()
    printWindow.print()
    printWindow.onafterprint = () => printWindow.close()
  })
}
