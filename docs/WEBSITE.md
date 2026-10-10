# GEP 官网发布

官网源码在 `site/`，静态站点部署分支为 `gh-pages`。

**仓库维护者仅需操作一次：**

1. 打开 [仓库 Pages 设置](https://github.com/Benjamindaoson/gep-agent-os/settings/pages)。
2. 在 **Build and deployment** 选择 **Deploy from a branch**。
3. 选择分支 **gh-pages**，目录 **/(root)**，点击 **Save**。
4. GitHub Pages 完成构建后，访问 **https://benjamindaoson.github.io/gep-agent-os/**。

以后修改 `site/` 并推送到 `main` 时，`.github/workflows/pages.yml` 会将网站文件同步到 `gh-pages`，GitHub Pages 会按所选来源自动重新发布。

当前助手对 GitHub 源码有写入权限，但 GitHub Actions Token 无权替仓库所有者自动开启 Pages 功能。网站地址只有 Pages 启用并部署成功后才正式可访问。

官网为**产品宣传站**，不等于 Cloud App 已正式上线。下载按钮指向真实的 GitHub Releases Alpha 版本。
