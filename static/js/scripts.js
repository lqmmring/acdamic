const content_dir = 'contents/'
const config_file = 'config.yml'
const section_names = ['home', 'news', 'experience', 'publications'];


window.addEventListener('DOMContentLoaded', event => {

    // Activate Bootstrap scrollspy on the main nav element
    const mainNav = document.body.querySelector('#mainNav');
    if (mainNav) {
        new bootstrap.ScrollSpy(document.body, {
            target: '#mainNav',
            offset: 74,
        });
    };

    // Collapse responsive navbar when toggler is visible
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });


    // Yaml
    fetch(content_dir + config_file)
        .then(response => response.text())
        .then(text => {
            const yml = jsyaml.load(text);
            Object.keys(yml).forEach(key => {
                try {
                    document.getElementById(key).innerHTML = yml[key];
                } catch {
                    console.log("Unknown id and value: " + key + "," + yml[key].toString())
                }

            })
        })
        .catch(error => console.log(error));


    // Marked
    marked.use({ mangle: false, headerIds: false })
    section_names.forEach((name, idx) => {
        fetch(content_dir + name + '.md')
            .then(response => {
                if (!response.ok) throw new Error(`Failed to load ${name}: ${response.status}`);
                return response.text();
            })
            .then(markdown => {
                const html = marked.parse(markdown);
                document.getElementById(name + '-md').innerHTML = html;
                if (name === 'news') {
                    const hasNews = Boolean(document.querySelector('#news-md li'));
                    if (!hasNews) {
                        document.getElementById('news-md').innerHTML = '<p>暂无新闻 / No news yet.</p>';
                    }
                }
                bootstrap.ScrollSpy.getInstance(document.body)?.refresh();
            }).then(() => {
                // MathJax
                if (window.MathJax?.typesetPromise) {
                    MathJax.typesetPromise([document.getElementById(name + '-md')])
                        .catch(error => console.log(error));
                }
            })
            .catch(error => {
                console.log(error);
                if (name === 'news' && !document.querySelector('#news-md li')) {
                    document.getElementById('news-md').innerHTML = '<p>新闻暂时无法加载，请稍后刷新 / Unable to load news. Please refresh later.</p>';
                }
            });
    })

}); 
