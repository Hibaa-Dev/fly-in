from typing import Any, List, Dict, Iterator, Tuple
import re


class Parser:
    """This class reads, process and validate the mapefile for a drone routing
    simulation.
    Attributes:
        file (str): Path to the target mapfile configuration text file.
        map (Dict[str, Any]): A structured nested dictionary collecting
            all successfully parsed simulation configurations
            (e.g., drone count, hubs, and connections).
        start_hub_counter (int): Tracked occurrences of 'start_hub' definitions
        end_hub_counter (int): Tracked occurrences of 'end_hub' definitions
        prefix (List[str]): Approved line action prefixes allowed
            by the text parser.
        zone_name (List[str]): Collected zone names used to ensure
            structural uniqueness.
        coordinate (List[Tuple[int, int]]): Tracked geometric positions
            to enforce spatial uniqueness.
        connection: Collect the bidirectional connections to ensure
            the same connection didn't appeare more than once
        hub_pattern (re.Pattern[str]): Compiled regular expression
            for hub string syntax.
        conn_pattern (re.Pattern[str]): Compiled regular
            expression for connection syntax.
    """

    def __init__(self, input_file: str) -> None:
        """Initializes the parser with the path to the file to parse.
        Args:
            input_file: Path to the configuration file that will be
                parsed by :meth:`check_input_file`.
        """
        self.file: str = input_file
        self.map: Dict[str, Any] = {
            'nb_drones': 0,
            'hubs': [],
            'connections': []
        }
        self.start_hub_counter: int = 0
        self.end_hub_counter: int = 0
        self.prefix: List[str] = ['start_hub', 'end_hub', 'hub', 'connection']
        self.zone_name: List[str] = []
        self.coordinate: List[str] = []
        self.connections: List[set[str | Any]] = []
        self.hub_pattern: re.Pattern[str] = re.compile(
            r"^(?P<name>[^\s-]+)\s+"
            r"(?P<x>-?\d+)\s+"
            r"(?P<y>-?\d+)"
            r"(?:\s+(\[(?P<attr>[^\]]*)\]))?$"
        )
        self.conn_pattern: re.Pattern[str] = re.compile(
                r"^(?P<source>[^\s-]+)-"
                r"(?P<target>[^\s-]+)"
                r"(?:\s+(\[(?P<metadata>[^\]]*)\]))?$"
        )

    def check_first_line(self, lines: Iterator[Tuple[int, str]]) -> None:
        """Validates and processes the mandatory first configuration
            row of the mapfile.

        This method ignores empty lines or trailing comments until
            it discovers the first operational parameter block.
            It explicitly checks for the mandatory 'nb_drones'
            format setting and saves the valid count into the map database.

        Args:
            lines (enumerate): An active line-by-line enumeration iterator
                tracking file reading progress.

        Raises:
            ValueError: If the file is entirely empty, or if the first valid
                operational statement doesn't conform to 'nb_drones:
                <positive_integer>'.
        """
        is_empty = True
        for nb_line, line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            is_empty = False
            if line.count(':') != 1:
                raise ValueError(f"Error on line {nb_line}: The first "
                                 "line must define the number of drones using "
                                 "nb_drones: <positive_integer>")
            key, value = line.split(":")
            key, value = key.strip(), value.strip()
            if key != "nb_drones" or not value.isdigit() or int(value) <= 0:
                raise ValueError(f"Error on line {nb_line}: The first "
                                 "line must define the number of drones using"
                                 "nb_drones: <positive_integer>")
            self.map["nb_drones"] = int(value)
            break
        if is_empty:
            raise ValueError("File cannot be empty")

    def check_start_end_hub(self, key: str, nb_line: int) -> None:
        """Ensures that exactly one origin node ('start_hub') andexactly one
            termination node ('end_hub') are specified across
            the layout mapfile.

        Args:
            key (str): The configuration identifier prefix extracted
                from the line.
            nb_line (int): Current processing line number for verbose
                error logging.

        Raises:
            ValueError: If a duplicate 'start_hub' or 'end_hub' prefix
                is processed.
        """
        if key == "start_hub":
            self.start_hub_counter += 1
            if self.start_hub_counter != 1:
                raise ValueError(f"Error on line {nb_line}: it must be "
                                 "exactly one start_hub")

        if key == "end_hub":
            self.end_hub_counter += 1
            if self.end_hub_counter != 1:
                raise ValueError(f"Error on line {nb_line}: it must be "
                                 "exactly one end_hub")

    def check_hub(self, value: str, nb_line: int) -> Dict[str, Any]:
        """Deconstructs and validates structural hub parameters
            via regex matching.

        Extracts layout details (name, coordinate pairs, metadata
            substrings) from the raw config input line. Checks
            that names are entirely original and tracks spatial
            positions to prevent layout collisions.

        Args:
            value (str): Raw string slice containing hub positional details.
            nb_line (int): Current processing line number for verbose
            error logging.

        Returns:
            dict: A key-value dictionary containing captured group names and
                matching regex values ('name', 'x', 'y', 'attr').

        Raises:
            ValueError: If layout syntax is corrupted, if a hub name is
                non-unique, or if multiple hubs share matching coordinate
                mappings.
        """
        info = re.fullmatch(self.hub_pattern, value)
        if not info:
            raise ValueError(f"Error on line {nb_line}: Invalid syntaxe!")
        if info.group('name') in self.zone_name:
            raise ValueError(f"Error on line {nb_line}: Zone name must be "
                             "unique")
        self.zone_name.append(info.group('name'))
        coordinate = info.group('x') + ', ' + info.group('y')
        if coordinate in self.coordinate:
            raise ValueError(f"Error on line {nb_line}: Duplicated coordinate")
        self.coordinate.append(coordinate)

        return info.groupdict()

    def check_hub_metadata(self, metadata: str,
                           nb_line: int) -> Dict[str, Any]:
        """Parses and sanitizes explicit configuration attributes
            enclosed in hub brackets.

        Iterates through custom tag pairings (e.g., zone, color, max_drones),
            ensuring attributes conform to safe validation bounds and type
            specifications. Converts numeric attributes to active Python
            integers.

        Args:
            metadata (str): Internal string content discovered within bracket
                anchors.
            nb_line (int): Current processing line number for verbose error
                logging.

        Returns:
            Dict[str, Any]: A sanitized dictionary containing valid overrides
                for explicit metadata fields.

        Raises:
            ValueError: If bracket configurations contain malformed syntax
                patterns, unknown attributes, invalid zone classification
                metrics, non-integer entries,
                negative values, or duplicated parameter labels.
        """

        zone_type: List[str] = ['normal', 'blocked', 'restricted', 'priority']
        parsed_meta: Dict[str, Any] = {}

        clean_metadata = re.sub(r'\s*=\s*', '=', metadata)
        for data in clean_metadata.split():
            if data.count('=') != 1:
                raise ValueError(f"Error on line {nb_line}: Invalide "
                                 "metadata, e.g [zone=... color=...]")

            key, value = data.split('=')
            key, value = key.strip(), value.strip()
            if key in parsed_meta:
                raise ValueError(f"Error on line {nb_line}: Duplicate "
                                 f"attribute definition'{key}' detected inside"
                                 " brackets")

            if key not in ['zone', 'color', 'max_drones']:
                raise ValueError(f"Error on line {nb_line}: Invalid metadata "
                                 "attribute")

            if key == 'zone':
                if value not in zone_type:
                    raise ValueError(f"Error on line {nb_line}: Invalid zone "
                                     "type")

            if key == 'color':
                if len(value.split()) != 1:
                    raise ValueError(f"Error on line {nb_line}: color must be "
                                     "a valid single-word strings")
            if key == 'max_drones':
                if not value.isdigit() or int(value) <= 0:
                    raise ValueError(f"Error on line {nb_line}: max_drones "
                                     "value must be positive integer")
                parsed_meta[key] = int(value)
                continue

            parsed_meta[key] = value

        return parsed_meta

    def check_conn(self, value: str, nb_line: int) -> Dict[str, Any]:
        """Parses and validates a connection line's value part.

        Matches ``value`` against ``self.conn_pattern`` (expected form
        ``source-target [metadata]``) and ensures both endpoints refer to
        zone names that were already declared by an earlier hub line.

        Args:
            value: The part of the line after the ``connection:`` prefix,
                e.g. ``"hub_1-hub_2 [max_link_capacity=5]"``.
            nb_line: The 1-based line number, used for error messages.

        Returns:
            A dict with the named groups from ``conn_pattern``: ``source``,
            ``target`` and ``metadata`` (the raw bracket contents, or
            ``None`` if no metadata was given).

        Raises:
            ValueError: If ``value`` does not match the expected
                connection syntax, or if ``source`` or ``target`` is not
                a previously declared zone name.
        """

        info = re.fullmatch(self.conn_pattern, value)
        if not info:
            raise ValueError(f"Error on line {nb_line}: Invalid connection "
                             "syntaxe")
        source = info.group("source")
        target = info.group("target")
        if source not in self.zone_name or target not in self.zone_name:
            raise ValueError(f"Error on line {nb_line}: connection must link "
                             "only previously defined zones")
        if info.group('source') == info.group('target'):
            raise ValueError(f"Error on line {nb_line}: Invalid connection")
        conn = {info.group('source'), info.group("target")}
        if conn in self.connections:
            raise ValueError(f"Error on line {nb_line}: The same connection "
                             "must not appear more than once ")
        self.connections.append(conn)

        return info.groupdict()

    def check_conn_metadata(self, metadata: str,
                            nb_line: int) -> Dict[str, Any]:
        """Parses and validates the bracketed metadata of a connection line.

        Expects space-separated ``key=value`` pairs. The only recognized
        key is ``max_link_capacity``, whose value must be a non-negative
        integer. Duplicate keys within the same brackets are rejected.

        Args:
            metadata: The raw contents between the square brackets, e.g.
                ``"max_link_capacity=5"``.
            nb_line: The 1-based line number, used for error messages.

        Returns:
            A dict containing the parsed ``max_link_capacity`` entry (as
            an ``int``) if present.

        Raises:
            ValueError: If an entry is not of the form ``key=value``, if
                a key is duplicated, if the key is not
                ``max_link_capacity``, or if its value is not a
                non-negative integer.
        """

        parsed_meta: Dict[str, Any] = {}

        clean_metadata = re.sub(r'\s*=\s*', '=', metadata)
        for data in clean_metadata.split():

            if data.count('=') != 1:
                raise ValueError(f"Error on line {nb_line}: Invalid metadata, "
                                 "correct syntaxe: [max_link_capacity=...]")

            key, value = data.split('=')
            key, value = key.strip(), value.strip()

            if key in parsed_meta:
                raise ValueError(f"Error on line {nb_line}: Duplicate "
                                 f"attribute definition '{key}' detected "
                                 "inside brackets")

            if key != 'max_link_capacity':
                raise ValueError(f"Error on line {nb_line}: Invalide metadata,"
                                 " correct syntaxe: [max_link_capacity=...]")

            if not value.isdigit() or int(value) < 0:
                raise ValueError(f"Error on line {nb_line}: max_link_capacity "
                                 "value must be positive integer")
            parsed_meta[key] = int(value)

        return parsed_meta

    def check_input_file(self) -> Dict[str, Any]:
        """Reads and parses the entire mapfile line-by-line.

        It skips comments and empty lines, validates the syntax of each hub
        and connection, fills in missing metadata with default values, and
        saves the fully structured data into the map dictionary.
        """
        with open(self.file) as file:
            lines = enumerate(file, start=1)
            self.check_first_line(lines)
            for nb_line, line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.count(':') != 1:
                    raise ValueError(f"Error on line {nb_line}: Invalid "
                                     "syntaxe!")
                key, value = line.split(':')
                key, value = key.strip(), value.strip()
                if key not in self.prefix:
                    raise ValueError(f"Error on line {nb_line}: Unknown "
                                     "prefix")

                self.check_start_end_hub(key, nb_line)

                if key in ('hub', 'start_hub', 'end_hub'):
                    hub_data = self.check_hub(value, nb_line)
                    hub_record = {
                        'type': key,
                        'zone_name': hub_data['name'],
                        'x': int(hub_data['x']),
                        'y': int(hub_data['y']),
                        'metadata': {'zone': 'normal', 'color': None,
                                     'max_drones': 1}
                    }
                    if hub_data['attr']:
                        hub_record['metadata'].update(self.check_hub_metadata(
                            hub_data['attr'], nb_line))
                    self.map['hubs'].append(hub_record)

                elif key == 'connection':
                    conn_data = self.check_conn(value, nb_line)
                    conn_record = {
                        'source': conn_data['source'],
                        'target': conn_data['target'],
                        'metadata': {'max_link_capacity': 1}
                    }
                    if conn_data['metadata']:
                        conn_record['metadata'] = self.check_conn_metadata(
                            conn_data['metadata'], nb_line)
                    self.map['connections'].append(conn_record)

            if self.start_hub_counter != 1 or self.end_hub_counter != 1:
                raise ValueError("Error: There must be exactly one start_hub: "
                                 "zone and one end_hub: zone.")
            return self.map
