from app.share.infrastructure.parsers.dof_parser import DOFHtmlParser


def test_dof_parser_does_not_split_on_inline_references():
    parser = DOFHtmlParser()
    html = """
    <html>
      <body>
        <span style="color:#A6802D">CÓDIGO DE PRUEBA</span>
        <p>TÍTULO PRIMERO</p>
        <p>Artículo 1.- Las obligaciones deberán cumplirse en tiempo y forma conforme al artículo 5 de este Código.</p>
        <p>Para efectos de este artículo, la autoridad competente resolverá conforme a derecho.</p>
        <p>Artículo 2.- El incumplimiento generará responsabilidad en términos de esta ley.</p>
      </body>
    </html>
    """

    articles = parser.parse(html)

    assert len(articles) == 2
    assert articles[0].numero_articulo == "Art. 1"
    assert "conforme al artículo 5" in articles[0].cuerpo_texto.lower()
    assert articles[1].numero_articulo == "Art. 2"
