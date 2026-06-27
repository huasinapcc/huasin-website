/**
 * 華昕藝心網站文章管理後台
 *
 * 部署時請選擇：
 *   執行身分：我
 *   存取權：只有我自己
 */

const CONFIG = Object.freeze({
  spreadsheetId: '1o0di_U7q_NKiDuwkHEnUqlX2QQNxAeXR1TKpAJl0WAQ',
  articleSheet: 'articles',
  therapistSheet: 'therapists',
  websiteUrl: 'https://www.hua-sin.com',
  imageFolderName: '華昕網站文章圖片',
  maxImageBytes: 8 * 1024 * 1024,
});

const ARTICLE_FIELDS = Object.freeze([
  'id',
  'title',
  'author_id',
  'category',
  'image_url',
  'summary',
  'content',
  'date',
  'active',
  'is_featured',
  'hashtags',
  'event_ended',
]);

function doGet() {
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('文章管理｜華昕藝心')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

/** 後台初次載入所需的全部資料。 */
function getBootData() {
  return {
    articles: listArticles_(),
    therapists: listTherapists_(),
    userEmail: Session.getActiveUser().getEmail() || '',
    websiteUrl: CONFIG.websiteUrl,
  };
}

/** 供部署後檢查資料連線，不會新增、編輯或刪除文章。 */
function healthCheck() {
  const articles = listArticles_();
  const therapists = listTherapists_();
  return {
    ok: true,
    articleCount: articles.length,
    publishedCount: articles.filter(article => article.active).length,
    therapistCount: therapists.length,
    checkedAt: Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
  };
}

/** 新增或更新文章。 */
function saveArticle(input) {
  const article = validateArticle_(input);
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);

  try {
    const sheet = getArticleSheet_();
    const headers = ensureArticleHeaders_(sheet);
    const index = headerIndex_(headers);
    const lastRow = sheet.getLastRow();
    const id = article.id || nextArticleId_(sheet, index);
    let rowNumber = 0;

    if (article.id) {
      rowNumber = findRowById_(sheet, index.id, article.id);
      if (!rowNumber) throw new Error('找不到這篇文章，可能已被移除，請重新整理。');
    } else {
      rowNumber = Math.max(lastRow + 1, 2);
    }

    // 同一時間只保留一篇精選文章。
    if (article.is_featured && sheet.getLastRow() >= 2) {
      sheet.getRange(2, index.is_featured + 1, sheet.getLastRow() - 1, 1).setValue(false);
    }

    const columnCount = sheet.getLastColumn();
    const existing = rowNumber <= sheet.getLastRow()
      ? sheet.getRange(rowNumber, 1, 1, columnCount).getValues()[0]
      : new Array(columnCount).fill('');

    const values = existing.slice();
    values[index.id] = id;
    values[index.title] = article.title;
    values[index.author_id] = article.author_id;
    values[index.category] = article.category;
    values[index.image_url] = article.image_url;
    values[index.summary] = article.summary;
    values[index.content] = article.content;
    values[index.date] = parseDate_(article.date);
    values[index.active] = article.active;
    values[index.is_featured] = article.is_featured;
    values[index.hashtags] = article.hashtags;
    values[index.event_ended] = article.event_ended;

    sheet.getRange(rowNumber, 1, 1, columnCount).setValues([values]);
    sheet.getRange(rowNumber, index.date + 1).setNumberFormat('yyyy/mm/dd');
    SpreadsheetApp.flush();

    return {
      ok: true,
      message: article.active ? '文章已發布' : '草稿已儲存',
      article: getArticleByRow_(sheet, headers, rowNumber),
    };
  } finally {
    lock.releaseLock();
  }
}

/** 保留文章與網址，只將它改為未發布。 */
function archiveArticle(id) {
  const numericId = Number(id);
  if (!Number.isFinite(numericId)) throw new Error('文章編號不正確。');

  const sheet = getArticleSheet_();
  const headers = ensureArticleHeaders_(sheet);
  const index = headerIndex_(headers);
  const rowNumber = findRowById_(sheet, index.id, numericId);
  if (!rowNumber) throw new Error('找不到這篇文章。');

  sheet.getRange(rowNumber, index.active + 1).setValue(false);
  sheet.getRange(rowNumber, index.is_featured + 1).setValue(false);
  SpreadsheetApp.flush();
  return { ok: true, message: '文章已下架', article: getArticleByRow_(sheet, headers, rowNumber) };
}

/** 將封面圖片上傳到專用 Google Drive 資料夾。 */
function uploadArticleImage(payload) {
  if (!payload || typeof payload.dataUrl !== 'string') throw new Error('沒有收到圖片。');
  const match = payload.dataUrl.match(/^data:(image\/(?:jpeg|png|webp|gif));base64,(.+)$/);
  if (!match) throw new Error('請上傳 JPG、PNG、WebP 或 GIF 圖片。');

  const bytes = Utilities.base64Decode(match[2]);
  if (bytes.length > CONFIG.maxImageBytes) throw new Error('圖片不可超過 8 MB。');

  const mimeType = match[1];
  const extension = mimeType === 'image/jpeg' ? 'jpg' : mimeType.split('/')[1];
  const safeBaseName = String(payload.fileName || 'article-image')
    .replace(/\.[^.]+$/, '')
    .replace(/[^\w\u3400-\u9fff-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 70) || 'article-image';
  const fileName = `${Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd-HHmmss')}-${safeBaseName}.${extension}`;
  const blob = Utilities.newBlob(bytes, mimeType, fileName);
  const folder = getImageFolder_();
  const file = folder.createFile(blob);

  try {
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  } catch (error) {
    file.setTrashed(true);
    throw new Error('目前 Google Workspace 不允許公開分享圖片，請調整 Drive 分享政策後再試。');
  }

  return {
    ok: true,
    id: file.getId(),
    name: file.getName(),
    url: `https://drive.google.com/file/d/${file.getId()}/view?usp=drive_link`,
    previewUrl: `https://drive.google.com/thumbnail?id=${file.getId()}&sz=w1200`,
  };
}

function listArticles_() {
  const sheet = getArticleSheet_();
  const headers = ensureArticleHeaders_(sheet);
  if (sheet.getLastRow() < 2) return [];

  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();
  return rows
    .map((row, i) => rowToArticle_(headers, row, i + 2))
    .filter(article => article.title || article.id)
    .sort((a, b) => String(b.date).localeCompare(String(a.date)) || Number(b.id) - Number(a.id));
}

function listTherapists_() {
  const book = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = book.getSheetByName(CONFIG.therapistSheet);
  if (!sheet || sheet.getLastRow() < 2) return [];

  const values = sheet.getDataRange().getValues();
  const headers = values.shift().map(normalizeHeader_);
  const index = headerIndex_(headers);

  return values
    .map(row => ({
      id: index.id == null ? '' : String(row[index.id] || ''),
      name: index.name == null ? '' : String(row[index.name] || ''),
      title: index.title == null ? '' : String(row[index.title] || ''),
    }))
    .filter(item => item.name)
    .sort((a, b) => Number(a.id || 9999) - Number(b.id || 9999));
}

function getArticleSheet_() {
  const book = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = book.getSheetByName(CONFIG.articleSheet);
  if (!sheet) throw new Error(`找不到「${CONFIG.articleSheet}」工作表。`);
  return sheet;
}

function ensureArticleHeaders_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, ARTICLE_FIELDS.length).setValues([ARTICLE_FIELDS]);
  }

  const lastColumn = Math.max(sheet.getLastColumn(), 1);
  const rawHeaders = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];
  const normalized = rawHeaders.map(normalizeHeader_);
  let nextColumn = rawHeaders.reduce((last, value, i) => value ? i + 2 : last, 1);

  ARTICLE_FIELDS.forEach(field => {
    if (!normalized.includes(field)) {
      sheet.getRange(1, nextColumn).setValue(field);
      normalized[nextColumn - 1] = field;
      nextColumn += 1;
    }
  });

  return sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(normalizeHeader_);
}

function normalizeHeader_(value) {
  const header = String(value || '').trim().toLowerCase();
  if (header === 'content\t') return 'content';
  return header;
}

function headerIndex_(headers) {
  return headers.reduce((result, header, index) => {
    if (header) result[header] = index;
    return result;
  }, {});
}

function rowToArticle_(headers, row, rowNumber) {
  const result = { rowNumber };
  headers.forEach((header, index) => {
    if (!header) return;
    let value = row[index];
    if (header === 'date' && value instanceof Date) {
      value = Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    }
    if (['active', 'is_featured', 'event_ended'].includes(header)) value = value === true || String(value).toUpperCase() === 'TRUE';
    result[header] = value == null ? '' : value;
  });

  ARTICLE_FIELDS.forEach(field => {
    if (!(field in result)) result[field] = ['active', 'is_featured', 'event_ended'].includes(field) ? false : '';
  });
  return result;
}

function getArticleByRow_(sheet, headers, rowNumber) {
  const row = sheet.getRange(rowNumber, 1, 1, sheet.getLastColumn()).getValues()[0];
  return rowToArticle_(headers, row, rowNumber);
}

function nextArticleId_(sheet, index) {
  if (sheet.getLastRow() < 2) return 1;
  const values = sheet.getRange(2, index.id + 1, sheet.getLastRow() - 1, 1).getValues().flat();
  return values.reduce((max, value) => Math.max(max, Number(value) || 0), 0) + 1;
}

function findRowById_(sheet, idColumnIndex, id) {
  if (sheet.getLastRow() < 2) return 0;
  const finder = sheet
    .getRange(2, idColumnIndex + 1, sheet.getLastRow() - 1, 1)
    .createTextFinder(String(id))
    .matchEntireCell(true)
    .findNext();
  return finder ? finder.getRow() : 0;
}

function validateArticle_(input) {
  if (!input || typeof input !== 'object') throw new Error('文章資料格式不正確。');
  const text = (key, max) => String(input[key] || '').trim().slice(0, max);
  const title = text('title', 180);
  const category = text('category', 50);
  const content = String(input.content || '').trim().slice(0, 100000);

  if (!title) throw new Error('請輸入文章標題。');
  if (!category) throw new Error('請選擇或輸入文章分類。');
  if (!content) throw new Error('請輸入文章內容。');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(input.date || ''))) throw new Error('請選擇文章日期。');

  return {
    id: input.id ? Number(input.id) : 0,
    title,
    author_id: text('author_id', 120),
    category,
    image_url: text('image_url', 1000),
    summary: String(input.summary || '').trim().slice(0, 1000),
    content,
    date: String(input.date),
    active: Boolean(input.active),
    is_featured: Boolean(input.is_featured),
    hashtags: text('hashtags', 500),
    event_ended: Boolean(input.event_ended),
  };
}

function parseDate_(value) {
  return Utilities.parseDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

function getImageFolder_() {
  const properties = PropertiesService.getScriptProperties();
  const existingId = properties.getProperty('ARTICLE_IMAGE_FOLDER_ID');
  if (existingId) {
    try {
      return DriveApp.getFolderById(existingId);
    } catch (error) {
      properties.deleteProperty('ARTICLE_IMAGE_FOLDER_ID');
    }
  }

  const folders = DriveApp.getFoldersByName(CONFIG.imageFolderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(CONFIG.imageFolderName);
  properties.setProperty('ARTICLE_IMAGE_FOLDER_ID', folder.getId());
  return folder;
}
