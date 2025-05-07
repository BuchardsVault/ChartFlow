
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ChartFlow</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <h1>ChartFlow</h1>
    <p>A Python DSL & interpreter for financial charts in your terminal</p>
    <nav>
      <a class="btn" href="https://github.com/BuchardsVault/ChartFlow" target="_blank">View on GitHub</a>
      <a class="btn outline" href="https://pypi.org/project/chartflow" target="_blank">Install via PyPI</a>
    </nav>
  </header>

  <main>
    <section>
      <h2>Getting Started</h2>
      <pre><code>pip install chartflow</code></pre>
      <p>Then run your <code>.cf</code> files:</p>
      <pre><code>chartflow myscript.cf</code></pre>
    </section>

    <section id="gallery">
      <h2>Screenshots</h2>
      <div class="gallery">
        <figure>
          <img src="images/tsla-candlestick.png" alt="TSLA candlestick chart">
          <figcaption>TSLA Candlestick</figcaption>
        </figure>
        <figure>
          <img src="images/grammar-diagram.png" alt="ChartFlow grammar diagram">
          <figcaption>Grammar & AST</figcaption>
        </figure>
        <figure>
          <img src="images/terminal-output.png" alt="Terminal output example">
          <figcaption>Terminal Table Output</figcaption>
        </figure>
        <figure>
          <img src="images/arnoldc-example.png" alt="ArnoldC homepage example">
          <figcaption>Inspiration: ArnoldC Site</figcaption>
        </figure>
      </div>
    </section>
  </main>

  <footer>
    <p>&copy; 2025 BuchardsVault</p>
  </footer>
</body>
</html>
