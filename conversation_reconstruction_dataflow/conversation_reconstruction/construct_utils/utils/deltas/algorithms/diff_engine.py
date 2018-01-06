"""
A :class:`deltas.DiffEngine` implements a streaming diff strategy that applies
a diff algorithm to a sequence of text revisions.  By maintaining an internal
state, various efficiencies can be implemented.

.. autoclass:: deltas.DiffEngine
    :members:
"""
import yamlconf


class DiffEngine:
    """
    Constructs a diff engine.
    """

    class Processor:
        """
        Constructs a new diff processor for processing many versions
        of a single text.
        """

        def process(text, token_class=None):
            raise NotImplementedError()

    def processor(self):
        """
        Configures and returns a new :class:`~deltas.DiffEngine.Processor`
        """
        raise NotImplementedError()

    @classmethod
    def from_config(cls, config, name, section_key="diff_engines"):
        """
        Constructs a :class:`deltas.DiffEngine` from a configuration
        doc.
        """
        section = config[section_key][name]
        if 'module' in section:
            return yamlconf.import_module(section['module'])
        else:
            Engine = yamlconf.import_module(section['class'])
            return Engine.from_config(config, name, section_key=section_key)
