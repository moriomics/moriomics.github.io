window.PORTFOLIO_PROJECTS = [
  {
    id: "openalex-literature-search",
    visible: true,
    featured: true,
    wide: false,
    title: "OpenAlex Literature Search",
    type: {
      ja: "Research tool",
      en: "Research tool"
    },
    description: {
      ja: "研究テーマに関連する文献をOpenAlexから検索し、被引用数、出版年、Open Access、撤回状態、抄録などを確認しながら候補論文を探索するWebアプリです。",
      en: "A literature-discovery web app that searches OpenAlex and helps review candidate papers using citation counts, publication year, Open Access status, retraction status, and abstracts."
    },
    technologies: ["HTML", "CSS", "JavaScript", "OpenAlex API", "localStorage"],
    webApp: "https://moriomics.github.io/openalex-literature-search/",
    github: "https://github.com/moriomics/openalex-literature-search"
  },
  {
    id: "mol-calculator",
    visible: true,
    featured: false,
    wide: false,
    title: "Molarity Calculator",
    type: {
      ja: "Laboratory tool",
      en: "Laboratory tool"
    },
    description: {
      ja: "CAS番号からPubChemの化学物質情報を確認し、モル濃度から必要秤量値、または秤量値からモル濃度を計算する実験支援Webアプリです。",
      en: "A laboratory calculation web app that looks up compound information from PubChem by CAS Registry Number and converts between molar concentration and required reagent mass."
    },
    technologies: ["HTML", "CSS", "JavaScript", "PubChem PUG REST API"],
    webApp: "https://moriomics.github.io/mol-calculator/",
    github: "https://github.com/moriomics/mol-calculator"
  },
  {
    id: "pdf-toolkit",
    visible: true,
    featured: false,
    wide: false,
    title: "PDF Toolkit",
    type: {
      ja: "Document tool",
      en: "Document tool"
    },
    description: {
      ja: "JPEG→PDF、PDFクロップ、OCR、PDF分割の4機能を、共通ナビゲーションと日本語/英語切り替えでまとめたブラウザベースのPDFツール集です。",
      en: "A browser-based PDF utility suite combining JPEG-to-PDF conversion, PDF cropping, OCR, and PDF splitting under shared navigation and bilingual UI."
    },
    technologies: ["HTML", "CSS", "JavaScript", "PDF.js", "pdf-lib", "Tesseract.js", "JSZip"],
    webApp: "https://moriomics.github.io/pdf-toolkit/",
    github: "https://github.com/moriomics/pdf-toolkit"
  },
  {
    id: "chatgpt-conversation-exporter",
    visible: true,
    featured: false,
    wide: false,
    title: "ChatGPT Conversation Exporter",
    type: {
      ja: "Chrome extension",
      en: "Chrome extension"
    },
    description: {
      ja: "ChatGPTの会話に含まれるプロンプトと回答を収集し、HTML保存と専用タブからのPDF印刷に対応するChrome拡張機能です。",
      en: "A Chrome extension that collects prompts and responses from a ChatGPT conversation, exports an HTML copy, and opens a dedicated tab for PDF printing."
    },
    technologies: ["JavaScript", "Chrome Extensions", "Manifest V3", "HTML", "CSS", "MathML"],
    webApp: null,
    github: "https://github.com/moriomics/chatgpt-conversation-exporter",
    note: {
      ja: "Chrome拡張機能 — インストールして利用",
      en: "Chrome extension — installation required"
    }
  },
  {
    "id": "local-transcriber",
    "visible": true,
    "featured": false,
    "wide": false,
    "title": "Local Transcriber",
    "type": {
      "ja": "Windows desktop application",
      "en": "Windows desktop application"
    },
    "description": {
      "ja": "録音済みの音声・動画をローカルで文字起こしするWindows向けアプリ。セグメント単位の編集、選択セルのコピー、TXT・SRT・JSON・Word出力と、確認後の任意のAI整形・要約に対応します。",
      "en": "A Windows desktop application for local transcription of recorded audio and video, with segment editing, selected-cell copying, TXT/SRT/JSON/Word export, and optional AI formatting and summarization after confirmation."
    },
    "technologies": [
      "Python 3.14",
      "PySide6",
      "faster-whisper",
      "CTranslate2",
      "FFmpeg",
      "OpenAI Responses API"
    ],
    "details": {
      "ja": [
        [
          "設計",
          "認識原文と編集文を分けて保持。音声認識は別プロセスで実行し、外部AIへのテキスト送信は確認後に限定。"
        ],
        [
          "検証状況",
          "Windows実機・GPU文字起こし・OpenAI実APIとの連携を確認済み。Linux / Python 3.14で自動テスト41件が合格。"
        ]
      ],
      "en": [
        [
          "Design",
          "Separate raw and edited text, recognition in a worker process, and explicit confirmation before text is sent to an external AI service."
        ],
        [
          "Validation",
          "Maintainer-verified Windows operation, GPU transcription, and live OpenAI API integration. 41 automated tests passed on Linux / Python 3.14."
        ]
      ]
    },
    "webApp": null,
    "github": "https://github.com/moriomics/local-transcriber",
    "note": {
      "ja": "Windows向けMVP — ソース公開・環境構築が必要",
      "en": "Windows MVP — source release; setup required"
    }
  },
  {
    id: "image-resizer",
    visible: true,
    featured: false,
    wide: false,
    title: "Image Resizer",
    type: {
      ja: "Image tool",
      en: "Image tool"
    },
    description: {
      ja: "複数画像のリサイズ、写真プリセット、PNG/JPEG出力、ZIP保存に対応したシンプルなブラウザベースの画像リサイズツールです。",
      en: "A lightweight browser-based image resizer supporting multiple images, photo presets, PNG/JPEG output, and ZIP download."
    },
    technologies: ["HTML", "CSS", "JavaScript", "Browser APIs"],
    webApp: "https://moriomics.github.io/image-resizer/",
    github: "https://github.com/moriomics/image-resizer"
  },
  {
    id: "trinary-image-app",
    visible: true,
    featured: false,
    wide: true,
    title: "Grayscale Trinarization Desktop App",
    type: {
      ja: "Desktop application",
      en: "Desktop application"
    },
    description: {
      ja: "画像を黒・グレー・白の3クラスへ分類するPython/Tkinterデスクトップアプリです。2しきい値版Otsu法、3値ノイズ除去・モルフォロジー、バッチ処理、CSV/Excel/ZIP出力に対応します。",
      en: "A Python/Tkinter desktop application that classifies grayscale images into black, gray, and white classes, with two-threshold Otsu, trinary denoising and morphology, batch processing, and CSV/Excel/ZIP export."
    },
    technologies: ["Python", "Tkinter", "NumPy", "Pillow", "openpyxl", "PyInstaller"],
    webApp: null,
    github: "https://github.com/moriomics/trinary-image-app",
    note: {
      ja: "デスクトップアプリ — ブラウザデモなし",
      en: "Desktop application — no browser demo"
    }
  },
  {
    id: "geo-age-expression",
    visible: true,
    featured: false,
    wide: true,
    title: "GEO Age-Associated Gene Expression Analysis",
    type: { ja: "Python / Jupyter解析ツール", en: "Python / Jupyter analysis tool" },
    description: {
      ja: "NCBI GEOの公開データから指定遺伝子を抽出し、年齢と発現量の関連を探索するNotebook。年齢を連続変数として扱う解析と、若年・高齢群の比較に対応します。",
      en: "A reusable Jupyter notebook for exploring associations between age and a selected gene's expression in public NCBI GEO data, using both continuous age and age-group comparisons."
    },
    technologies: ["Python", "Jupyter", "GEOparse", "pandas", "SciPy", "statsmodels", "Matplotlib"],
    details: {
      ja: [
        ["目的・入力", "GSE IDとNCBI Gene IDを指定して発現量と年齢情報を取得。"],
        ["解析", "OLS回帰、Spearman相関、若年・高齢群のWelchのt検定。CSV・PNG出力。"],
        ["検証", "データセットに応じて年齢メタデータ、対象試料、発現値の尺度を確認する必要があります。検証済みGSEの網羅的な一覧は未掲載です。"],
        ["制約", "マイクロアレイと一部のbulk RNA-seq形式に対応。RNA-seqの探索的比較はカウントベースの差次的発現解析の代替ではありません。"],
        ["再現方法", "公開Notebookとrequirements.txtを用意。GSE・Gene IDを設定して実行し、必要に応じて発現行列を指定します。"]
      ],
      en: [
        ["Goal / input", "Set a GSE accession and NCBI Gene ID to obtain expression and age metadata."],
        ["Methods", "OLS regression, Spearman correlation, and Welch's t-test for younger versus older groups; CSV and PNG exports."],
        ["Verification", "Age metadata, specimen selection, and expression scale must be checked per dataset. No comprehensive list of validated GSE accessions is published."],
        ["Limitations", "Supports microarray and selected bulk RNA-seq formats. Exploratory RNA-seq comparisons do not replace count-based differential expression analysis."],
        ["Reproducibility", "Notebook and requirements.txt are public. Set GSE / Gene ID and provide a local expression matrix if needed."]
      ]
    },
    webApp: null,
    github: "https://github.com/moriomics/geo-age-expression-analysis",
    note: { ja: "Jupyter Notebook — ブラウザデモなし", en: "Jupyter Notebook — no browser demo" }
  },
  {
    id: "geo-disease-expression",
    visible: true,
    featured: false,
    wide: true,
    title: "GEO Normal–Disease Gene Expression Analysis",
    type: { ja: "Python / Jupyter解析ツール", en: "Python / Jupyter analysis tool" },
    description: {
      ja: "NCBI GEOデータから指定遺伝子の発現量を取得し、健常群と疾患群を探索的に比較するNotebook。メタデータからの群判定を試み、必要に応じて手動指定できます。",
      en: "A reusable Jupyter notebook for exploratory normal-versus-disease comparisons of a selected gene in NCBI GEO datasets. It attempts metadata-based group labeling, with a manual override option."
    },
    technologies: ["Python", "Jupyter", "GEOparse", "pandas", "SciPy", "statsmodels", "Matplotlib"],
    details: {
      ja: [
        ["目的・入力", "GSE IDとNCBI Gene IDを指定。サンプルの診断情報から群を推定し、CSVで群ラベルを上書き可能。"],
        ["解析", "健常・疾患2群の発現比較。必要に応じて年齢・性別などの共変量を指定できます。"],
        ["検証", "群ラベルの自動判定結果を監査用CSVで確認してから解釈します。自動分類がすべてのGSEで正しいことは保証されません。"],
        ["制約", "比較群の定義、組織・採取条件、発現値の尺度に依存します。データセットによって追加設定や手動確認が必要です。"],
        ["再現方法", "公開Notebookとrequirements.txtを使用。GSE・Gene IDを設定し、生成された監査ファイルを確認します。"]
      ],
      en: [
        ["Goal / input", "Set GSE and NCBI Gene ID. Group labels are inferred from sample metadata when possible and can be overridden using CSV."],
        ["Methods", "Normal-versus-disease expression comparison with optional age / sex covariates."],
        ["Verification", "Review generated audit CSV files before interpretation; automatic group labeling is not guaranteed to be correct for every GSE."],
        ["Limitations", "Results depend on group definitions, tissue and collection conditions, and expression scale. Some datasets require manual configuration."],
        ["Reproducibility", "Notebook and requirements.txt are public. Configure GSE / Gene ID and inspect the generated audit files."]
      ]
    },
    webApp: null,
    github: "https://github.com/moriomics/geo-disease-expression-analysis",
    note: { ja: "Jupyter Notebook — ブラウザデモなし", en: "Jupyter Notebook — no browser demo" }
  }
];

