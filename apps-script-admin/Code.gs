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
  therapistImageFolderName: '華昕網站心理師照片',
  defaultAdminEmail: 'huasin.apcc@gmail.com',
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

const THERAPIST_FIELDS = Object.freeze([
  'id',
  'name',
  'title',
  'license_no',
  'photo_url',
  'current_positions',
  'education',
  'experience',
  'certifications',
  'philosophy',
  'specialties',
  'articles',
  'social_links',
  'active',
  'sort_order',
]);

function doGet() {
  const email = currentUserEmail_();
  if (!isAdminEmail_(email)) {
    return HtmlService.createHtmlOutput(`<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>無法進入後台</title><style>body{min-height:100vh;margin:0;display:grid;place-items:center;background:#f3f7f7;color:#334e5c;font-family:sans-serif}.box{max-width:520px;padding:40px;border-radius:18px;background:#fff;box-shadow:0 16px 50px rgba(40,70,80,.12);text-align:center}h1{font-size:24px}p{line-height:1.8;color:#71808a}</style></head><body><main class="box"><h1>這個帳號沒有後台權限</h1><p>目前登入帳號：${escapeServerHtml_(email || '無法辨識')}<br>請由既有管理員在「帳號管理」中加入此 Gmail。</p></main></body></html>`)
      .setTitle('無法進入後台｜華昕藝心')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  }
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('文章管理｜華昕藝心')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

/** 後台初次載入所需的全部資料。 */
function getBootData() {
  assertAuthorized_();
  return {
    articles: listArticles_(),
    therapists: listTherapists_(),
    admins: getAdminEmails_(),
    userEmail: Session.getActiveUser().getEmail() || '',
    websiteUrl: CONFIG.websiteUrl,
  };
}

/** 供部署後檢查資料連線，不會新增、編輯或刪除文章。 */
function healthCheck() {
  assertAuthorized_();
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
  assertAuthorized_();
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
  assertAuthorized_();
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

/** 新增或更新心理師。 */
function saveTherapist(input) {
  assertAuthorized_();
  const therapist = validateTherapist_(input);
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);

  try {
    const sheet = getTherapistSheet_();
    const headers = ensureTherapistHeaders_(sheet);
    const index = headerIndex_(headers);
    const lastRow = sheet.getLastRow();
    const id = therapist.id || nextTherapistId_(sheet, index);
    let rowNumber = 0;

    if (therapist.id) {
      rowNumber = findRowById_(sheet, index.id, therapist.id);
      if (!rowNumber) throw new Error('找不到這位心理師，可能已被移除，請重新整理。');
    } else {
      rowNumber = Math.max(lastRow + 1, 2);
    }

    const columnCount = sheet.getLastColumn();
    const existing = rowNumber <= sheet.getLastRow()
      ? sheet.getRange(rowNumber, 1, 1, columnCount).getValues()[0]
      : new Array(columnCount).fill('');
    const values = existing.slice();

    THERAPIST_FIELDS.forEach(field => {
      values[index[field]] = field === 'id' ? id : therapist[field];
    });

    sheet.getRange(rowNumber, 1, 1, columnCount).setValues([values]);
    SpreadsheetApp.flush();
    return {
      ok: true,
      message: therapist.active ? '心理師資料已上架' : '心理師資料已儲存',
      therapist: getTherapistByRow_(sheet, headers, rowNumber),
    };
  } finally {
    lock.releaseLock();
  }
}

/** 保留心理師資料，只從前台下架。 */
function archiveTherapist(id) {
  assertAuthorized_();
  const numericId = Number(id);
  if (!Number.isFinite(numericId)) throw new Error('心理師編號不正確。');
  const sheet = getTherapistSheet_();
  const headers = ensureTherapistHeaders_(sheet);
  const index = headerIndex_(headers);
  const rowNumber = findRowById_(sheet, index.id, numericId);
  if (!rowNumber) throw new Error('找不到這位心理師。');

  sheet.getRange(rowNumber, index.active + 1).setValue(false);
  SpreadsheetApp.flush();
  return { ok: true, message: '心理師已下架', therapist: getTherapistByRow_(sheet, headers, rowNumber) };
}

/** 將封面圖片上傳到專用 Google Drive 資料夾。 */
function uploadArticleImage(payload) {
  assertAuthorized_();
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

/** 將心理師照片上傳到專用 Google Drive 資料夾。 */
function uploadTherapistPhoto(payload) {
  assertAuthorized_();
  if (!payload || typeof payload.dataUrl !== 'string') throw new Error('沒有收到照片。');
  const match = payload.dataUrl.match(/^data:(image\/(?:jpeg|png|webp));base64,(.+)$/);
  if (!match) throw new Error('請上傳 JPG、PNG 或 WebP 照片。');
  const bytes = Utilities.base64Decode(match[2]);
  if (bytes.length > CONFIG.maxImageBytes) throw new Error('照片不可超過 8 MB。');

  const mimeType = match[1];
  const extension = mimeType === 'image/jpeg' ? 'jpg' : mimeType.split('/')[1];
  const safeBaseName = String(payload.fileName || 'therapist-photo')
    .replace(/\.[^.]+$/, '')
    .replace(/[^\w\u3400-\u9fff-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 70) || 'therapist-photo';
  const fileName = `${Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd-HHmmss')}-${safeBaseName}.${extension}`;
  const file = getTherapistImageFolder_().createFile(Utilities.newBlob(bytes, mimeType, fileName));

  try {
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  } catch (error) {
    file.setTrashed(true);
    throw new Error('目前 Google Workspace 不允許公開分享照片，請調整 Drive 分享政策後再試。');
  }

  return {
    ok: true,
    id: file.getId(),
    name: file.getName(),
    url: `https://drive.google.com/file/d/${file.getId()}/view?usp=drive_link`,
    previewUrl: `https://drive.google.com/thumbnail?id=${file.getId()}&sz=w800`,
  };
}

/** 新增後台管理員，並分享後台所需的 Google 檔案。 */
function addAdminEmail(inputEmail) {
  assertAuthorized_();
  const email = normalizeEmail_(inputEmail);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error('請輸入有效的 Google 帳號 Email。');
  const emails = getAdminEmails_();
  if (emails.includes(email)) {
    return { ok: true, message: `${email} 已經是管理員`, admins: emails };
  }
  emails.push(email);
  saveAdminEmails_(emails);

  try {
    DriveApp.getFileById(CONFIG.spreadsheetId).addEditor(email);
    getImageFolder_().addEditor(email);
    getTherapistImageFolder_().addEditor(email);
  } catch (error) {
    saveAdminEmails_(emails.filter(item => item !== email));
    throw new Error('無法分享資料權限給這個帳號，請確認 Email 正確且 Google Drive 允許分享。');
  }
  return { ok: true, message: `已新增管理員 ${email}`, admins: getAdminEmails_() };
}

/** 移除後台管理員；主帳號不可移除。 */
function removeAdminEmail(inputEmail) {
  assertAuthorized_();
  const email = normalizeEmail_(inputEmail);
  if (email === normalizeEmail_(CONFIG.defaultAdminEmail)) throw new Error('主帳號不可移除。');
  if (email === currentUserEmail_()) throw new Error('不可移除目前正在使用的帳號。');
  const emails = getAdminEmails_().filter(item => item !== email);
  saveAdminEmails_(emails);

  try { DriveApp.getFileById(CONFIG.spreadsheetId).removeEditor(email); } catch (error) {}
  try { getImageFolder_().removeEditor(email); } catch (error) {}
  try { getTherapistImageFolder_().removeEditor(email); } catch (error) {}
  return { ok: true, message: `已移除管理員 ${email}`, admins: getAdminEmails_() };
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
  const sheet = getTherapistSheet_();
  const headers = ensureTherapistHeaders_(sheet);
  if (sheet.getLastRow() < 2) return [];
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();
  return rows
    .map((row, i) => rowToTherapist_(headers, row, i + 2))
    .filter(item => item.name || item.id)
    .sort((a, b) => Number(a.sort_order || a.id || 9999) - Number(b.sort_order || b.id || 9999));
}

function getArticleSheet_() {
  const book = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = book.getSheetByName(CONFIG.articleSheet);
  if (!sheet) throw new Error(`找不到「${CONFIG.articleSheet}」工作表。`);
  return sheet;
}

function getTherapistSheet_() {
  const book = SpreadsheetApp.openById(CONFIG.spreadsheetId);
  const sheet = book.getSheetByName(CONFIG.therapistSheet);
  if (!sheet) throw new Error(`找不到「${CONFIG.therapistSheet}」工作表。`);
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

function ensureTherapistHeaders_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, THERAPIST_FIELDS.length).setValues([THERAPIST_FIELDS]);
  }
  const lastColumn = Math.max(sheet.getLastColumn(), 1);
  const rawHeaders = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];
  const normalized = rawHeaders.map(normalizeHeader_);
  let nextColumn = rawHeaders.reduce((last, value, i) => value ? i + 2 : last, 1);
  THERAPIST_FIELDS.forEach(field => {
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

function rowToTherapist_(headers, row, rowNumber) {
  const result = { rowNumber };
  headers.forEach((header, index) => {
    if (!header) return;
    let value = row[index];
    if (header === 'active') value = value === true || String(value).toUpperCase() === 'TRUE';
    result[header] = value == null ? '' : value;
  });
  THERAPIST_FIELDS.forEach(field => {
    if (!(field in result)) result[field] = field === 'active' ? false : '';
  });
  return result;
}

function getTherapistByRow_(sheet, headers, rowNumber) {
  const row = sheet.getRange(rowNumber, 1, 1, sheet.getLastColumn()).getValues()[0];
  return rowToTherapist_(headers, row, rowNumber);
}

function nextArticleId_(sheet, index) {
  if (sheet.getLastRow() < 2) return 1;
  const values = sheet.getRange(2, index.id + 1, sheet.getLastRow() - 1, 1).getValues().flat();
  return values.reduce((max, value) => Math.max(max, Number(value) || 0), 0) + 1;
}

function nextTherapistId_(sheet, index) {
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

function validateTherapist_(input) {
  if (!input || typeof input !== 'object') throw new Error('心理師資料格式不正確。');
  const text = (key, max) => String(input[key] || '').trim().slice(0, max);
  const name = text('name', 80);
  const title = text('title', 150);
  if (!name) throw new Error('請輸入心理師姓名。');
  if (!title) throw new Error('請輸入專業職稱。');

  return {
    id: input.id ? Number(input.id) : 0,
    name,
    title,
    license_no: text('license_no', 200),
    photo_url: text('photo_url', 1000),
    current_positions: String(input.current_positions || '').trim().slice(0, 10000),
    education: String(input.education || '').trim().slice(0, 10000),
    experience: String(input.experience || '').trim().slice(0, 30000),
    certifications: String(input.certifications || '').trim().slice(0, 20000),
    philosophy: String(input.philosophy || '').trim().slice(0, 20000),
    specialties: String(input.specialties || '').trim().slice(0, 20000),
    articles: String(input.articles || '').trim().slice(0, 20000),
    social_links: String(input.social_links || '').trim().slice(0, 3000),
    active: Boolean(input.active),
    sort_order: Number(input.sort_order) || Number(input.id) || 999,
  };
}

function parseDate_(value) {
  return Utilities.parseDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

function currentUserEmail_() {
  return normalizeEmail_(Session.getActiveUser().getEmail());
}

function normalizeEmail_(value) {
  return String(value || '').trim().toLowerCase();
}

function getAdminEmails_() {
  const stored = PropertiesService.getScriptProperties().getProperty('ADMIN_EMAILS');
  const emails = stored ? stored.split(',').map(normalizeEmail_).filter(Boolean) : [];
  const primary = normalizeEmail_(CONFIG.defaultAdminEmail);
  if (!emails.includes(primary)) emails.unshift(primary);
  return [...new Set(emails)];
}

function saveAdminEmails_(emails) {
  const normalized = [...new Set(emails.map(normalizeEmail_).filter(Boolean))];
  const primary = normalizeEmail_(CONFIG.defaultAdminEmail);
  if (!normalized.includes(primary)) normalized.unshift(primary);
  PropertiesService.getScriptProperties().setProperty('ADMIN_EMAILS', normalized.join(','));
}

function isAdminEmail_(email) {
  return Boolean(email) && getAdminEmails_().includes(normalizeEmail_(email));
}

function assertAuthorized_() {
  const email = currentUserEmail_();
  if (!isAdminEmail_(email)) throw new Error('這個 Google 帳號沒有後台權限。');
  return email;
}

function escapeServerHtml_(value) {
  return String(value || '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
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

function getTherapistImageFolder_() {
  const properties = PropertiesService.getScriptProperties();
  const existingId = properties.getProperty('THERAPIST_IMAGE_FOLDER_ID');
  if (existingId) {
    try {
      return DriveApp.getFolderById(existingId);
    } catch (error) {
      properties.deleteProperty('THERAPIST_IMAGE_FOLDER_ID');
    }
  }
  const folders = DriveApp.getFoldersByName(CONFIG.therapistImageFolderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(CONFIG.therapistImageFolderName);
  properties.setProperty('THERAPIST_IMAGE_FOLDER_ID', folder.getId());
  return folder;
}
