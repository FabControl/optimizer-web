from django.utils.translation import gettext_lazy as _

# this section is used for automatic translation generation only
if False:
    parameter_names = [
            _("Bridging extrusion multiplier"),
            _("Bridging part cooling"),
            _("Bridging printing speed"),
            _("Chamber temperature"),
            _("Coasting distance"),
            _("Exit ventilation power"),
            _("Extrusion multiplier"),
            _("Extrusion temperature"),
            _("First-layer extrusion temperature"),
            _("First-layer printing speed"),
            _("First-layer track height"),
            _("First-layer track width"),
            _("Part cooling"),
            _("Print bed coating"),
            _("Print bed temperature"),
            _("Printing speed"),
            _("Retraction distance"),
            _("Retraction speed"),
            _("Retraction-restart distance"),
            _("Track height"),
            _("Track width"),
            _("Z-offset"),
            ]

    paramater_help_texts = [
            _("For this test this value is equal to unity, but, if needed, it can be tested in a separate test"),
            _("Set a value from the range 20-50 mm/s for printing flexible materials, or 30-70 mm/s for printing harder materials"),
            _("Set part cooling. Active part cooling is required when printing using high deposition rates or when printing fine details"),
            _("Set the range of <b>Retraction distances</b> to be tested"),
            _("Set the range to 10-25 mm/s for printing flexible materials, or 15-35 mm/s for harder materials"),
            _("Set the range to 20-50 mm/s for printing flexible materials, or to 30-70 mm/s for printing harder materials"),
            _("Set the range to 5-15 mm/s for printing flexible materials, or to 10-30 mm/s for printing harder materials"),
            _("Set this value to proceed"),
            _("Set this value to proceed. Perform the corresponding test to fine-tune this value"),
            _("Set this value to proceed. This value will determine the resolution and surface quality of your print"),
            _("The default value is equal to the nozzle inner diameter, but you can perform the corresponding test to fine-tune this value"),
            _("These seven values will be tested at four <b>Printing speeds</b>. You can change the limiting values"),
            _("These seven values will be tested at four different <b>Bridging printing speeds</b> (see below). You can change the limiting values"),
            _("These seven values will be tested at four different <b>First-layer printing speeds</b> (see below). You can change the limiting values"),
            _("These seven values will be tested at four different <b>Printing speeds</b> (see below). You can change the limiting values"),
            _("These seven values will be tested at four different <b>Retraction distances</b> (see below). You can change the limiting values"),
            _("These seven values will be tested at four different <b>Retraction speeds</b> (see below). You can change the limiting values"),
            _("These seven values will be tested at one <b>First-layer printing speed</b>. You can change the limiting values"),
            _("These seven values will be tested at one <b>Printing speed</b>. You can change the limiting values"),
            _("These seven values will be tested while all other processing parameters are constant. You can change the limiting values"),
            _("These seven values will be tested. You can change the limiting values"),
            _("This value was determined in the previous test(s) and cannot be changed"),
            ]

    test_init_hints = [
            _("This is a core test which helps finding a working retraction distance under general conditions."),
            _("This is an additional test to avoid under-extrusion."),
            _("This test helps you find a base temperature and printing speed. These will be optimized further in later tests. Since there can be different parameter combinations that work, but are not optimal for your intended target, this is an essential test."),
            _("This test is needed to arrive at the most optimal flow-rate."),
            _("This test is needed to avoid gaps between tracks and find the limits of horizontal resolution with a given nozzle."),
            _("This test is needed to avoid stringing."),
            _("This test is needed to establish good first layer printing settings. A good first layer is essential to achieving good prints."),
            _("This test is needed to find Z-offset value in case of non-level print bed or printbed coating."),
            _("This test is needed to find reliable settings for retraction. The best combination of 3 parameters are determined simulataneously."),
            _("This test is needed to find the best bridging settings."),
            _("This test is needed to find the best retraction restart distance and coasting settings."),
            _("This test is needed to find the limits of printing resolution (layer thickness)."),
            _("This test is needed to solve possible issues with adhesion between tracks if there are any. Good weld-together is essential to achieving good mechanical properties in any printed part."
                "<br>Run it only if you see the voids in between the tracks in the previous test. By skipping this test, the <b>First-layer-track-width</b> value will be set to the <b>Nozzle inner diameter</b>"),
            ]

    test_validation_hints = [
            _("<ul><li>If the print does not adhere to the build platform, increase the <b>First-layer extrusion temperature</b> and re-run the test.</li>"
              "<li>If this does not help, increase the <b>Printbed temperature</b> or apply different coating/spray on the build platform.</li>"
              "<li>If you cannot find acceptable combination of two parameters, re-run the test with different <b>First-layer-extrusion-temperature</b> value and/or using different <b>Printing-speed</b> range.</li></ul>"),
            ]

    test_names = [
            _("Z-Offset"),
            _("First-Layer Track Height vs First-Layer Printing Speed"),
            _("First-Layer Track Width"),
            _("Extrusion Temperature vs Printing Speed"),
            _("Track Height vs Printing Speed"),
            _("Track Width"),
            _("Extrusion Multiplier"),
            _("Printing Speed"),
            _("Extrusion Temperature vs Retraction Distance"),
            _("Retraction Distance vs Printing Speed"),
            _("Retraction Distance"),
            _("Retraction Distance vs Retraction Speed"),
            _("Retraction Restart Distance vs Printing Speed And Coasting Distance"),
            _("Bridging Extrusion Multiplier vs Bridging Printing Speed"),
            _("Soluble Support Adhesion"),
            ]

    formatted_test_names = [
            _("Z-Offset"),
            _("First-Layer Track Height vs<br>First-Layer Printing Speed"),
            _("First-Layer Track Width"),
            _("Extrusion Temperature vs<br>Printing Speed"),
            _("Track Height vs<br>Printing Speed"),
            _("Track Width"),
            _("Extrusion Multiplier"),
            _("Printing Speed"),
            _("Extrusion Temperature vs<br>Retraction Distance"),
            _("Retraction Distance vs<br>Printing Speed"),
            _("Retraction Distance"),
            _("Retraction Distance vs<br>Retraction Speed"),
            _("Retraction Restart Distance vs<br>Printing Speed And Coasting Distance"),
            _("Bridging Extrusion Multiplier vs<br>Bridging Printing Speed"),
            _("Soluble Support Adhesion"),
            ]
