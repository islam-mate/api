import { defineConfig } from 'vitepress'

export default defineConfig({
  base: process.env.READTHEDOCS_CANONICAL_URL
    ? new URL(process.env.READTHEDOCS_CANONICAL_URL).pathname
    : '/',
  title: 'Islam Mate API',
  ignoreDeadLinks: true,

  sitemap: {
    hostname: 'https://islam-mate-api.readthedocs.io'
  },

  head: [
    ['meta', { name: 'keywords', content: 'islamic api, prayer times api, quran api, hadith api, azkar api, qibla api, hijri calendar api, fastapi, python, open source, muslim developer, arabic api' }],
    ['meta', { name: 'author', content: 'Youssef Mekkkawy' }],
    ['meta', { name: 'robots', content: 'index, follow' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'Islam Mate API' }],
    ['meta', { property: 'og:title', content: 'Islam Mate API — Open-source Islamic REST API' }],
    ['meta', { property: 'og:description', content: 'Open-source Islamic REST API for Muslim developers. Prayer times, Quran, Hadith, Azkar, Qibla, Hijri Calendar and more. Built with FastAPI + Python.' }],
    ['meta', { property: 'og:url', content: 'https://islam-mate-api.readthedocs.io' }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
    ['meta', { name: 'twitter:title', content: 'Islam Mate API — Open-source Islamic REST API' }],
    ['meta', { name: 'twitter:description', content: 'Prayer times, Quran, Hadith, Azkar, Qibla and more. Free Islamic REST API built with FastAPI.' }],
    ['link', { rel: 'canonical', href: 'https://islam-mate-api.readthedocs.io' }],
  ],
  description: 'Open-source Islamic REST API for Muslim developers',
  lang: 'en',

  locales: {
    root: {
      label: 'English',
      lang: 'en',
      dir: 'ltr'
    },
    ar: {
      label: 'العربية',
      lang: 'ar',
      dir: 'rtl',
      link: '/ar/',
      title: 'Islam Mate API',
  ignoreDeadLinks: true,

  sitemap: {
    hostname: 'https://islam-mate-api.readthedocs.io'
  },

  head: [
    ['meta', { name: 'keywords', content: 'islamic api, prayer times api, quran api, hadith api, azkar api, qibla api, hijri calendar api, fastapi, python, open source, muslim developer, arabic api' }],
    ['meta', { name: 'author', content: 'Youssef Mekkkawy' }],
    ['meta', { name: 'robots', content: 'index, follow' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'Islam Mate API' }],
    ['meta', { property: 'og:title', content: 'Islam Mate API — Open-source Islamic REST API' }],
    ['meta', { property: 'og:description', content: 'Open-source Islamic REST API for Muslim developers. Prayer times, Quran, Hadith, Azkar, Qibla, Hijri Calendar and more. Built with FastAPI + Python.' }],
    ['meta', { property: 'og:url', content: 'https://islam-mate-api.readthedocs.io' }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
    ['meta', { name: 'twitter:title', content: 'Islam Mate API — Open-source Islamic REST API' }],
    ['meta', { name: 'twitter:description', content: 'Prayer times, Quran, Hadith, Azkar, Qibla and more. Free Islamic REST API built with FastAPI.' }],
    ['link', { rel: 'canonical', href: 'https://islam-mate-api.readthedocs.io' }],
  ],
      description: 'واجهة برمجية اسلامية مفتوحة المصدر',
      themeConfig: {
        nav: [
          { text: 'الرئيسية', link: '/ar/' },
          { text: 'البداية السريعة', link: '/ar/getting-started' },
          { text: 'نقاط النهاية', items: [
            { text: 'اوقات الصلاة', link: '/ar/endpoints/prayer-times' },
            { text: 'القبلة', link: '/ar/endpoints/qibla' },
            { text: 'التقويم الهجري', link: '/ar/endpoints/hijri' },
            { text: 'رمضان', link: '/ar/endpoints/ramadan' },
            { text: 'الاذكار', link: '/ar/endpoints/azkar' },
            { text: 'الادعية', link: '/ar/endpoints/dua' },
            { text: 'اسماء الله الحسنى', link: '/ar/endpoints/allah-names' },
            { text: 'الحديث', link: '/ar/endpoints/hadith' },
          ]},
          { text: 'ادلة', items: [
            { text: 'كيفية الاستخدام', link: '/ar/guides/how-to-use' },
            { text: 'رياضيات الصلاة', link: '/ar/guides/prayer-time-math' },
          ]},
          { text: 'المساهمة', link: '/ar/contributing/index' },
        ],
        sidebar: {
          '/ar/': [
            { text: 'المقدمة', items: [
              { text: 'البداية السريعة', link: '/ar/getting-started' },
              { text: 'المصادقة', link: '/ar/authentication' },
              { text: 'تحديد المعدل', link: '/ar/rate-limiting' },
            ]},
            { text: 'نقاط النهاية', items: [
              { text: 'اوقات الصلاة', link: '/ar/endpoints/prayer-times' },
              { text: 'القبلة', link: '/ar/endpoints/qibla' },
              { text: 'التقويم الهجري', link: '/ar/endpoints/hijri' },
              { text: 'رمضان', link: '/ar/endpoints/ramadan' },
              { text: 'الاذكار', link: '/ar/endpoints/azkar' },
              { text: 'الادعية', link: '/ar/endpoints/dua' },
              { text: 'اسماء الله الحسنى', link: '/ar/endpoints/allah-names' },
              { text: 'الحديث', link: '/ar/endpoints/hadith' },
            ]},
            { text: 'ادلة', items: [
              { text: 'كيفية الاستخدام', link: '/ar/guides/how-to-use' },
              { text: 'رياضيات الصلاة', link: '/ar/guides/prayer-time-math' },
            ]},
            { text: 'المساهمة', items: [
              { text: 'كيفية المساهمة', link: '/ar/contributing/index' },
              { text: 'اضافة وحدة جديدة', link: '/ar/contributing/new-module' },
              { text: 'تشغيل الاختبارات', link: '/ar/contributing/tests' },
              { text: 'هيكل المشروع', link: '/ar/contributing/architecture' },
            ]},
          ]
        }
      }
    }
  },

  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/en/getting-started' },
      { text: 'Endpoints', items: [
        { text: 'Prayer Times', link: '/en/endpoints/prayer-times' },
        { text: 'Qibla', link: '/en/endpoints/qibla' },
        { text: 'Hijri Calendar', link: '/en/endpoints/hijri' },
        { text: 'Ramadan', link: '/en/endpoints/ramadan' },
        { text: 'Azkar', link: '/en/endpoints/azkar' },
        { text: 'Dua', link: '/en/endpoints/dua' },
        { text: 'Allah Names', link: '/en/endpoints/allah-names' },
        { text: 'Hadith', link: '/en/endpoints/hadith' },
      ]},
      { text: 'Guides', items: [
        { text: 'How to Use', link: '/en/guides/how-to-use' },
        { text: 'Prayer Time Math', link: '/en/guides/prayer-time-math' },
      ]},
      { text: 'Contributing', link: '/en/contributing/index' },
    ],

    sidebar: {
      '/en/': [
        { text: 'Introduction', items: [
          { text: 'Getting Started', link: '/en/getting-started' },
          { text: 'Authentication', link: '/en/authentication' },
          { text: 'Rate Limiting', link: '/en/rate-limiting' },
        ]},
        { text: 'Endpoints', items: [
          { text: 'Prayer Times', link: '/en/endpoints/prayer-times' },
          { text: 'Qibla', link: '/en/endpoints/qibla' },
          { text: 'Hijri Calendar', link: '/en/endpoints/hijri' },
          { text: 'Ramadan', link: '/en/endpoints/ramadan' },
          { text: 'Azkar', link: '/en/endpoints/azkar' },
          { text: 'Dua', link: '/en/endpoints/dua' },
          { text: 'Allah Names', link: '/en/endpoints/allah-names' },
          { text: 'Hadith', link: '/en/endpoints/hadith' },
        ]},
        { text: 'Guides', items: [
          { text: 'How to Use the API', link: '/en/guides/how-to-use' },
          { text: 'Prayer Time Math', link: '/en/guides/prayer-time-math' },
        ]},
        { text: 'Contributing', items: [
          { text: 'How to Contribute', link: '/en/contributing/index' },
          { text: 'New Module', link: '/en/contributing/new-module' },
          { text: 'Running Tests', link: '/en/contributing/tests' },
          { text: 'Architecture', link: '/en/contributing/architecture' },
        ]},
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Youssef-Mekkkawy/islam-mate-api' }
    ],

    search: { provider: 'local' },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright 2026 Youssef Mekkkawy'
    }
  }
})
