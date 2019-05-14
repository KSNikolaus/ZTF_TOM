# lcomultifilter.py
from tom_observations.facilities.lco import LCOFacility
from tom_observations.facilities.lco import LCOFacility, LCOObservationForm, filter_choices
from django import forms
from tom_observations.facilities.lco import LCOFacility, LCOObservationForm, filter_choices
from django import forms
from crispy_forms.layout import Div


class LCOMultiFilterFacility(LCOFacility):
    name = 'LCOMultiFilter'


class LCOMultiFilterForm(LCOObservationForm):
    filter2 = forms.ChoiceField(choices=filter_choices)
    exposure_time2 = forms.FloatField(min_value=0.1)
    filter3 = forms.ChoiceField(choices=filter_choices)
    exposure_time3 = forms.FloatField(min_value=0.1)

    def layout(self):
        return Div(
                Div(
                    Div(
                        'group_id', 'proposal', 'ipp_value', 'observation_type', 'start', 'end',
                        css_class='col'
                    ),
                    Div(
                        'instrument_name', 'exposure_count', 'max_airmass',
                        css_class='col'
                    ),
                    css_class='form-row'
                ),
                Div(
                    Div(
                        'filter', 'exposure_time',
                        css_class='col'
                    ),
                    Div(
                        'filter2', 'exposure_time2',
                        css_class='col'
                    ),
                    Div(
                        'filter3', 'exposure_time3',
                        css_class='col'
                    ),
                    css_class='form-row'
                )
        )

    def observation_payload(self):
        payload = super().observation_payload()
        molecule2 = payload['requests'][0]['molecules'][0].copy()
        molecule3 = payload['requests'][0]['molecules'][0].copy()

        molecule2['filter'] = self.cleaned_data['filter2']
        molecule2['exposure_time'] = self.cleaned_data['exposure_time2']
        molecule3['filter'] = self.cleaned_data['filter3']
        molecule3['exposure_time'] = self.cleaned_data['exposure_time3']

        payload['requests'][0]['molecules'].extend([molecule2, molecule3])
        return payload


class LCOMultiFilterFacility(LCOFacility):
    name = 'LCOMultiFilter'
    form = LCOMultiFilterForm
