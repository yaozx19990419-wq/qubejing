document.addEventListener("alpine:init", () => {
  Alpine.data("appData", () => ({
    mode: "demo", // 'demo', 'single', 'batch'
    sliderValue: 50,
    isProcessing: false,
    processingText: "AI is processing magic...",
    batchCount: 0,

    // 【新增】背景颜色控制
    bgColor: "transparent", // 默认透明
    copyBtnText: "Copy",

    images: {
      original:
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-4.0.3&w=800&q=80",
      processed:
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-4.0.3&w=800&q=80",
    },
    singleFileName: "demo-image.jpg",
    batchZipBlob: null,

    triggerUpload() {
      this.$refs.fileInput.click();
    },

    reset() {
      this.mode = "demo";
      this.isProcessing = false;
      this.bgColor = "transparent"; // 重置颜色
      this.$refs.fileInput.value = "";
      this.images.original =
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-4.0.3&w=800&q=80";
      this.images.processed = this.images.original;
    },

    async handleFileUpload(event) {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      // 1. 数量限制
      if (files.length > 10) {
        alert("⚠️ Limit Exceeded: Max 10 images.");
        this.$refs.fileInput.value = "";
        return;
      }

      // 2. 大小限制
      const MAX_SIZE_MB = 10;
      for (let i = 0; i < files.length; i++) {
        if (files[i].size > MAX_SIZE_MB * 1024 * 1024) {
          alert(`⚠️ File Too Large: Max ${MAX_SIZE_MB}MB.`);
          this.$refs.fileInput.value = "";
          return;
        }
      }

      this.isProcessing = true;

      if (files.length === 1) {
        this.mode = "single";
        this.processingText = "Processing single image...";
        this.singleFileName = files[0].name;
        // 重置背景色为透明
        this.bgColor = "transparent";
        await this.processSingle(files[0]);
      } else {
        this.mode = "batch";
        this.batchCount = files.length;
        this.processingText = `Processing ${files.length} images...`;
        await this.processBatch(files);
      }
    },

    async processSingle(file) {
      this.images.original = URL.createObjectURL(file);
      this.images.processed = this.images.original;

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("http://localhost:8000/api/remove-bg", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) throw new Error("Failed");

        const blob = await response.blob();
        this.images.processed = URL.createObjectURL(blob);

        setTimeout(
          () =>
            document
              .getElementById("demo")
              .scrollIntoView({ behavior: "smooth" }),
          100
        );
      } catch (error) {
        console.error("Error:", error);
        alert("Processing failed. Check backend.");
      } finally {
        this.isProcessing = false;
      }
    },

    async processBatch(files) {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
      }

      try {
        const response = await fetch(
          "http://localhost:8000/api/remove-bg-batch",
          {
            method: "POST",
            body: formData,
          }
        );

        if (!response.ok) throw new Error("Batch failed");

        this.batchZipBlob = await response.blob();
        setTimeout(
          () =>
            document
              .getElementById("demo")
              .scrollIntoView({ behavior: "smooth" }),
          100
        );
      } catch (e) {
        console.error(e);
        alert("Batch processing failed.");
        this.mode = "demo";
      } finally {
        this.isProcessing = false;
      }
    },

    // 【核心升级】下载逻辑：支持合成背景色
    async downloadSingle() {
      if (this.mode === "demo") return;

      // 如果是透明背景，直接下载原逻辑
      if (this.bgColor === "transparent") {
        const link = document.createElement("a");
        link.href = this.images.processed;
        link.download = this.getDownloadName();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        // 如果有背景色，需要 Canvas 合成
        await this.downloadWithBackground();
      }
    },

    // 使用 Canvas 合成背景
    async downloadWithBackground() {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.src = this.images.processed;

      await new Promise((resolve) => (img.onload = resolve));

      const canvas = document.createElement("canvas");
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d");

      // 1. 填充背景色
      ctx.fillStyle = this.bgColor;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 2. 绘制前景图
      ctx.drawImage(img, 0, 0);

      // 3. 导出并下载
      const link = document.createElement("a");
      link.download = this.getDownloadName("jpg"); // 有背景色通常存为 JPG 比较小，或者 PNG 也可以
      link.href = canvas.toDataURL("image/jpeg", 0.9); // 0.9 质量
      link.click();
    },

    // 【新增】一键复制到剪贴板
    async copyImage() {
      try {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.src = this.images.processed;
        await new Promise((resolve) => (img.onload = resolve));

        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");

        // 如果有背景色，先画背景
        if (this.bgColor !== "transparent") {
          ctx.fillStyle = this.bgColor;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
        ctx.drawImage(img, 0, 0);

        canvas.toBlob(async (blob) => {
          await navigator.clipboard.write([
            new ClipboardItem({ "image/png": blob }),
          ]);
          // 按钮反馈动画
          this.copyBtnText = "Copied!";
          setTimeout(() => (this.copyBtnText = "Copy"), 2000);
        });
      } catch (err) {
        console.error(err);
        alert("Copy failed. Try downloading instead.");
      }
    },

    getDownloadName(ext) {
      const nameWithoutExt =
        this.singleFileName.substring(
          0,
          this.singleFileName.lastIndexOf(".")
        ) || this.singleFileName;
      // 如果没传扩展名，默认用 png
      return `${nameWithoutExt}-ClearBG.${ext || "png"}`;
    },

    downloadBatch() {
      if (!this.batchZipBlob) return;
      const link = document.createElement("a");
      link.href = URL.createObjectURL(this.batchZipBlob);
      link.download = "ClearBG-Batch-Images.zip";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
  }));
});
