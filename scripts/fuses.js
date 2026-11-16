// 读取 / 关闭 Electron 的 asar 完整性校验 fuse，让改过 app.asar 的程序能正常启动。
const { flipFuses, getCurrentFuseWire, FuseVersion, FuseV1Options } = require('@electron/fuses');

const exe = process.argv[2];
const mode = process.argv[3] || 'show';

(async () => {
  if (!exe) {
    console.error('usage: node fuses.js <exe> [show|disable-asar]');
    process.exit(2);
  }
  const wire = await getCurrentFuseWire(exe);
  console.log('fuse version:', wire.version);
  console.log('EnableEmbeddedAsarIntegrityValidation:', wire[FuseV1Options.EnableEmbeddedAsarIntegrityValidation]);

  if (mode === 'disable-asar') {
    await flipFuses(exe, {
      version: FuseVersion.V1,
      resetAdHocDarwinSignature: true,
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: false,
    });
    const after = await getCurrentFuseWire(exe);
    console.log('after:', after[FuseV1Options.EnableEmbeddedAsarIntegrityValidation]);
  }
})().catch((e) => {
  console.error('ERR', e.message);
  process.exit(1);
});
