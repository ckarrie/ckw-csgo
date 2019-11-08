/*
        var currentBackground = 0;
        var backgrounds = [];
        backgrounds[0] = '{% static "csgomatches/backgrounds/IMG_6232.JPG" %}';
        backgrounds[1] = '{% static "csgomatches/backgrounds/IMG_6239.JPG" %}';
        backgrounds[2] = 'images/BasePic3.jpg';
        backgrounds[3] = 'images/BasePic4.jpg';
        backgrounds[4] = 'images/BasePic5.jpg';

        function changeBackground() {
            currentBackground++;
            if (currentBackground > 4) currentBackground = 0;
            $('body').fadeOut(1500, function () {
                $('body').css({
                    'background-image': "url('" + backgrounds[currentBackground] + "')"
                });
                $('body').fadeIn(1500);
            });


            setTimeout(changeBackground, 5000);
        }
        */