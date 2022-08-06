# coding: utf8
from __future__ import unicode_literals, division, print_function

import csv
import os
import random
import shutil
from timeit import default_timer as timer

from spacy import about
from spacy import util
from spacy.compat import path2str
from spacy.errors import Errors
from spacy.gold import GoldCorpus
from spacy.lookups import Lookups
from spacy.util import use_gpu as set_gpu
import srsly
from thinc.neural._classes.model import Model
import tqdm
from wasabi import msg

num_iteration = -1
max_iterations = -1

#     lang=("Model language", "positional", None, str),
#     output_path=("Output directory to store model in", "positional", None, Path),
#     train_path=("Location of JSON-formatted training data", "positional", None, Path),
#     dev_path=("Location of JSON-formatted development data", "positional", None, Path),
#     raw_text=("Path to jsonl file with unlabelled text documents.", "option", "rt", Path),
#     base_model=("Name of model to update (optional)", "option", "b", str),
#     pipeline=("Comma-separated names of pipeline components", "option", "p", str),
#     replace_components=("Replace components from base model", "flag", "R", bool),
#     vectors=("Model to load vectors from", "option", "v", str),
#     width=("Width of CNN layers of Tok2Vec component", "option", "cw", int),
#     conv_depth=("Depth of CNN layers of Tok2Vec component", "option", "cd", int),
#     cnn_window=("Window size for CNN layers of Tok2Vec component", "option", "cW", int),
#     cnn_pieces=("Maxout size for CNN layers of Tok2Vec component. 1 for Mish", "option", "cP", int),
#     use_chars=("Whether to use character-based embedding of Tok2Vec component", "flag", "chr", bool),
#     bilstm_depth=("Depth of BiLSTM layers of Tok2Vec component (requires PyTorch)", "option", "lstm", int),
#     embed_rows=("Number of embedding rows of Tok2Vec component", "option", "er", int),
#     n_iter=("Number of iterations", "option", "n", int),
#     n_early_stopping=("Maximum number of training epochs without dev accuracy improvement", "option", "ne", int),
#     n_examples=("Number of examples", "option", "ns", int),
#     use_gpu=("Use GPU", "option", "g", int),
#     version=("Model version", "option", "V", str),
#     meta_path=("Optional path to meta.json to use as base.", "option", "m", Path),
#     init_tok2vec=("Path to pretrained weights for the token-to-vector parts of the models.
#     parser_multitasks=("Side objectives for parser CNN, e.g. 'dep' or 'dep,tag'", "option", "pt", str),
#     entity_multitasks=("Side objectives for NER CNN, e.g. 'dep' or 'dep,tag'", "option", "et", str),
#     noise_level=("Amount of corruption for data augmentation", "option", "nl", float),
#     orth_variant_level=("Amount of orthography variation for data augmentation", "option", "ovl", float),
#     eval_beam_widths=("Beam widths to evaluate, e.g. 4,8", "option", "bw", str),
#     gold_preproc=("Use gold preprocessing", "flag", "G", bool),
#     learn_tokens=("Make parser learn gold-standard tokenization", "flag", "T", bool),
#     textcat_multilabel=("Textcat classes aren't mutually exclusive (multilabel)", "flag", "TML", bool),
#     textcat_arch=("Textcat model architecture", "option", "ta", str),
#     textcat_positive_label=("Textcat positive label for binary classes with two labels", "option", "tpl", str),
#     tag_map_path=("Location of JSON-formatted tag map", "option", "tm", Path),
#     omit_extra_lookups=("Don't include extra lookups in model", "flag", "OEL", bool),
#     verbose=("Display more information for debug", "flag", "VV", bool),
def train(lang, output_path, train_path, dev_path, raw_text=None, base_model=None, pipeline="tagger,parser,ner", replace_components=False,
          vectors=None, width=96, conv_depth=4, cnn_window=1, cnn_pieces=3, use_chars=False, bilstm_depth=0, embed_rows=2000,
          n_iter=30, n_early_stopping=None, n_examples=0, use_gpu=-1, version="0.0.0", meta_path=None, init_tok2vec=None,
          parser_multitasks="", entity_multitasks="", noise_level=0.0, orth_variant_level=0.0, eval_beam_widths="", gold_preproc=False,
          learn_tokens=False, textcat_multilabel=False, textcat_arch="bow", textcat_positive_label=None, tag_map_path=None,
          omit_extra_lookups=False, verbose=False, dropout_from=0.1, dropout_to=0.5, batch_from=100.0, batch_to=1000.0):
    global num_iteration
    num_iteration = 0
    global max_iterations
    max_iterations = n_iter

    util.fix_random_seed()
    util.set_env_log(verbose)

    # Make sure all files and paths exists if they are needed
    train_path = util.ensure_path(train_path)
    dev_path = util.ensure_path(dev_path)
    meta_path = util.ensure_path(meta_path)
    output_path = util.ensure_path(output_path)
    if raw_text is not None:
        raw_text = list(srsly.read_jsonl(raw_text))
    if not train_path or not train_path.exists():
        msg.fail("Training data not found", train_path, exits=1)
    if not dev_path or not dev_path.exists():
        msg.fail("Development data not found", dev_path, exits=1)
    if meta_path is not None and not meta_path.exists():
        msg.fail("Can't find model meta.json", meta_path, exits=1)
    meta = srsly.read_json(meta_path) if meta_path else {}
    if not output_path.exists():
        output_path.mkdir()

    # Take dropout and batch size as generators of values -- dropout
    # starts high and decays sharply, to force the optimizer to explore.
    dropout_rates = util.decaying(
        dropout_from,
        dropout_to,
        util.env_opt("dropout_decay", 0.0),
    )
    batch_sizes = util.compounding(
        batch_from,
        batch_to,
        util.env_opt("batch_compound", 1.001),
    )

    if not eval_beam_widths:
        eval_beam_widths = [1]
    else:
        eval_beam_widths = [int(bw) for bw in eval_beam_widths.split(",")]
        if 1 not in eval_beam_widths:
            eval_beam_widths.append(1)
        eval_beam_widths.sort()
    has_beam_widths = eval_beam_widths != [1]

    # Set up the base model and pipeline. If a base model is specified, load
    # the model and make sure the pipeline matches the pipeline setting. If
    # training starts from a blank model, intitalize the language class.
    pipeline = [p.strip() for p in pipeline.split(",")]
    disabled_pipes = None
    pipes_added = False
    if use_gpu >= 0:
        activated_gpu = None
        try:
            activated_gpu = set_gpu(use_gpu)
        except Exception as e:
            msg.warn("Exception: {}".format(e))
        if activated_gpu is not None:
            msg.text("Using GPU: {}".format(use_gpu))
        else:
            msg.warn("Unable to activate GPU: {}".format(use_gpu))
            msg.text("Using CPU only")
            use_gpu = -1
    base_components = []
    if base_model:
        nlp = util.load_model(base_model)
        if nlp.lang != lang:
            msg.fail(
                "Model language ('{}') doesn't match language specified as "
                "`lang` argument ('{}') ".format(nlp.lang, lang),
                exits=1,
            )
        for pipe in pipeline:
            pipe_cfg = {}
            if pipe == "parser":
                pipe_cfg = {"learn_tokens": learn_tokens}
            elif pipe == "textcat":
                pipe_cfg = {
                    "exclusive_classes": not textcat_multilabel,
                    "architecture": textcat_arch,
                    "positive_label": textcat_positive_label,
                }
            if pipe not in nlp.pipe_names:
                msg.text("Adding component to base model: '{}'".format(pipe))
                nlp.add_pipe(nlp.create_pipe(pipe, config=pipe_cfg))
                pipes_added = True
            elif replace_components:
                msg.text("Replacing component from base model '{}'".format(pipe))
                nlp.replace_pipe(pipe, nlp.create_pipe(pipe, config=pipe_cfg))
                pipes_added = True
            else:
                if pipe == "textcat":
                    textcat_cfg = nlp.get_pipe("textcat").cfg
                    base_cfg = {
                        "exclusive_classes": textcat_cfg["exclusive_classes"],
                        "architecture": textcat_cfg["architecture"],
                        "positive_label": textcat_cfg["positive_label"],
                    }
                    if base_cfg != pipe_cfg:
                        msg.fail(
                            "The base textcat model configuration does"
                            "not match the provided training options. "
                            "Existing cfg: {}, provided cfg: {}".format(
                                base_cfg, pipe_cfg
                            ),
                            exits=1,
                        )
                base_components.append(pipe)
        disabled_pipes = nlp.disable_pipes(
            [p for p in nlp.pipe_names if p not in pipeline]
        )
    else:
        msg.text("Starting with blank model '{}'".format(lang))
        lang_cls = util.get_lang_class(lang)
        nlp = lang_cls()
        for pipe in pipeline:
            if pipe == "parser":
                pipe_cfg = {"learn_tokens": learn_tokens}
            elif pipe == "textcat":
                pipe_cfg = {
                    "exclusive_classes": not textcat_multilabel,
                    "architecture": textcat_arch,
                    "positive_label": textcat_positive_label,
                }
            else:
                pipe_cfg = {}
            nlp.add_pipe(nlp.create_pipe(pipe, config=pipe_cfg))

    if tag_map_path is not None:
        tag_map = srsly.read_json(tag_map_path)
        # Replace tag map with provided mapping
        nlp.vocab.morphology.load_tag_map(tag_map)

    # Create empty extra lexeme tables so the data from spacy-lookups-data
    # isn't loaded if these features are accessed
    if omit_extra_lookups:
        nlp.vocab.lookups_extra = Lookups()
        nlp.vocab.lookups_extra.add_table("lexeme_cluster")
        nlp.vocab.lookups_extra.add_table("lexeme_prob")
        nlp.vocab.lookups_extra.add_table("lexeme_settings")

    if vectors:
        msg.text("Loading vector from model '{}'".format(vectors))
        _load_vectors(nlp, vectors)

    # Multitask objectives
    multitask_options = [("parser", parser_multitasks), ("ner", entity_multitasks)]
    for pipe_name, multitasks in multitask_options:
        if multitasks:
            if pipe_name not in pipeline:
                msg.fail(
                    "Can't use multitask objective without '{}' in the "
                    "pipeline".format(pipe_name)
                )
            pipe = nlp.get_pipe(pipe_name)
            for objective in multitasks.split(","):
                pipe.add_multitask_objective(objective)

    # Prepare training corpus
    corpus = GoldCorpus(train_path, dev_path, limit=n_examples)
    n_train_words = corpus.count_train()

    if base_model and not pipes_added:
        # Start with an existing model, use default optimizer
        optimizer = nlp.resume_training(device=use_gpu)
    else:
        # Start with a blank model, call begin_training
        cfg = {"device": use_gpu}
        cfg["conv_depth"] = conv_depth
        cfg["token_vector_width"] = width
        cfg["bilstm_depth"] = bilstm_depth
        cfg["cnn_maxout_pieces"] = cnn_pieces
        cfg["embed_size"] = embed_rows
        cfg["conv_window"] = cnn_window
        cfg["subword_features"] = not use_chars
        optimizer = nlp.begin_training(lambda: corpus.train_tuples, **cfg)

    nlp._optimizer = None

    # Load in pretrained weights
    if init_tok2vec is not None:
        components = _load_pretrained_tok2vec(nlp, init_tok2vec, base_components)
        msg.text("Loaded pretrained tok2vec for: {}".format(components))

    # Verify textcat config
    if "textcat" in pipeline:
        textcat_labels = nlp.get_pipe("textcat").cfg.get("labels", [])
        if textcat_positive_label and textcat_positive_label not in textcat_labels:
            msg.fail(
                "The textcat_positive_label (tpl) '{}' does not match any "
                "label in the training data.".format(textcat_positive_label),
                exits=1,
            )
        if textcat_positive_label and len(textcat_labels) != 2:
            msg.fail(
                "A textcat_positive_label (tpl) '{}' was provided for training "
                "data that does not appear to be a binary classification "
                "problem with two labels.".format(textcat_positive_label),
                exits=1,
            )
        train_docs = corpus.train_docs(
            nlp,
            noise_level=noise_level,
            gold_preproc=gold_preproc,
            max_length=0,
            ignore_misaligned=True,
        )
        train_labels = set()
        if textcat_multilabel:
            multilabel_found = False
            for text, gold in train_docs:
                train_labels.update(gold.cats.keys())
                if list(gold.cats.values()).count(1.0) != 1:
                    multilabel_found = True
            if not multilabel_found and not base_model:
                msg.warn(
                    "The textcat training instances look like they have "
                    "mutually-exclusive classes. Remove the flag "
                    "'--textcat-multilabel' to train a classifier with "
                    "mutually-exclusive classes."
                )
        if not textcat_multilabel:
            for text, gold in train_docs:
                train_labels.update(gold.cats.keys())
                if list(gold.cats.values()).count(1.0) != 1 and not base_model:
                    msg.warn(
                        "Some textcat training instances do not have exactly "
                        "one positive label. Modifying training options to "
                        "include the flag '--textcat-multilabel' for classes "
                        "that are not mutually exclusive."
                    )
                    nlp.get_pipe("textcat").cfg["exclusive_classes"] = False
                    textcat_multilabel = True
                    break
        if base_model and set(textcat_labels) != train_labels:
            msg.fail(
                "Cannot extend textcat model using data with different "
                "labels. Base model labels: {}, training data labels: "
                "{}.".format(textcat_labels, list(train_labels)),
                exits=1,
            )
        if textcat_multilabel:
            msg.text(
                "Textcat evaluation score: ROC AUC score macro-averaged across "
                "the labels '{}'".format(", ".join(textcat_labels))
            )
        elif textcat_positive_label and len(textcat_labels) == 2:
            msg.text(
                "Textcat evaluation score: F1-score for the "
                "label '{}'".format(textcat_positive_label)
            )
        elif len(textcat_labels) > 1:
            if len(textcat_labels) == 2:
                msg.warn(
                    "If the textcat component is a binary classifier with "
                    "exclusive classes, provide '--textcat-positive-label' for "
                    "an evaluation on the positive class."
                )
            msg.text(
                "Textcat evaluation score: F1-score macro-averaged across "
                "the labels '{}'".format(", ".join(textcat_labels))
            )
        else:
            msg.fail(
                "Unsupported textcat configuration. Use `spacy debug-data` "
                "for more information."
            )

    # fmt: off
    row_head, output_stats = _configure_training_output(pipeline, use_gpu, has_beam_widths)
    try:
        iter_since_best = 0
        best_score = 0.0
        for i in range(n_iter):
            num_iteration = i + 1
            train_docs = corpus.train_docs(
                nlp,
                noise_level=noise_level,
                orth_variant_level=orth_variant_level,
                gold_preproc=gold_preproc,
                max_length=0,
                ignore_misaligned=True,
            )
            if raw_text:
                random.shuffle(raw_text)
                raw_batches = util.minibatch(
                    (nlp.make_doc(rt["text"]) for rt in raw_text), size=8
                )
            words_seen = 0
            with tqdm.tqdm(total=n_train_words, leave=False) as pbar:
                losses = {}
                for batch in util.minibatch_by_words(train_docs, size=batch_sizes):
                    if not batch:
                        continue
                    docs, golds = zip(*batch)
                    try:
                        nlp.update(
                            docs,
                            golds,
                            sgd=optimizer,
                            drop=next(dropout_rates),
                            losses=losses,
                        )
                    except ValueError as e:
                        err = "Error during training"
                        if init_tok2vec:
                            err += " Did you provide the same parameters during 'train' as during 'pretrain'?"
                        msg.fail(err, "Original error message: {}".format(e), exits=1)
                    if raw_text:
                        # If raw text is available, perform 'rehearsal' updates,
                        # which use unlabelled data to reduce overfitting.
                        # noinspection PyUnboundLocalVariable
                        raw_batch = list(next(raw_batches))
                        nlp.rehearse(raw_batch, sgd=optimizer, losses=losses)
                    if not int(os.environ.get("LOG_FRIENDLY", 0)):
                        pbar.update(sum(len(doc) for doc in docs))
                    words_seen += sum(len(doc) for doc in docs)
            with nlp.use_params(optimizer.averages):
                util.set_env_log(False)
                epoch_model_path = output_path / ("model%d" % i)
                nlp.to_disk(epoch_model_path)
                nlp_loaded = util.load_model_from_path(epoch_model_path)
                for beam_width in eval_beam_widths:
                    for name, component in nlp_loaded.pipeline:
                        if hasattr(component, "cfg"):
                            component.cfg["beam_width"] = beam_width
                    dev_docs = list(
                        corpus.dev_docs(
                            nlp_loaded,
                            gold_preproc=gold_preproc,
                            ignore_misaligned=True,
                        )
                    )
                    nwords = sum(len(doc_gold[0]) for doc_gold in dev_docs)
                    start_time = timer()
                    scorer = nlp_loaded.evaluate(dev_docs, verbose=verbose)
                    end_time = timer()
                    if use_gpu < 0:
                        gpu_wps = None
                        cpu_wps = nwords / (end_time - start_time)
                    else:
                        gpu_wps = nwords / (end_time - start_time)
                        # Only evaluate on CPU in the first iteration (for
                        # timing) if GPU is enabled
                        if i == 0:
                            with Model.use_device("cpu"):
                                nlp_loaded = util.load_model_from_path(epoch_model_path)
                                for name, component in nlp_loaded.pipeline:
                                    if hasattr(component, "cfg"):
                                        component.cfg["beam_width"] = beam_width
                                dev_docs = list(
                                    corpus.dev_docs(
                                        nlp_loaded,
                                        gold_preproc=gold_preproc,
                                        ignore_misaligned=True,
                                    )
                                )
                                start_time = timer()
                                scorer = nlp_loaded.evaluate(dev_docs, verbose=verbose)
                                end_time = timer()
                                cpu_wps = nwords / (end_time - start_time)
                    acc_loc = output_path / ("model%d" % i) / "accuracy.json"
                    srsly.write_json(acc_loc, scorer.scores)

                    # Update model meta.json
                    meta["lang"] = nlp.lang
                    meta["pipeline"] = nlp.pipe_names
                    meta["spacy_version"] = ">=%s" % about.__version__
                    if beam_width == 1:
                        meta["speed"] = {
                            "nwords": nwords,
                            "cpu": cpu_wps,
                            "gpu": gpu_wps,
                        }
                        meta.setdefault("accuracy", {})
                        for component in nlp.pipe_names:
                            for metric in _get_metrics(component):
                                meta["accuracy"][metric] = scorer.scores[metric]
                    else:
                        meta.setdefault("beam_accuracy", {})
                        meta.setdefault("beam_speed", {})
                        for component in nlp.pipe_names:
                            for metric in _get_metrics(component):
                                meta["beam_accuracy"][metric] = scorer.scores[metric]
                        meta["beam_speed"][beam_width] = {
                            "nwords": nwords,
                            "cpu": cpu_wps,
                            "gpu": gpu_wps,
                        }
                    meta["vectors"] = {
                        "width": nlp.vocab.vectors_length,
                        "vectors": len(nlp.vocab.vectors),
                        "keys": nlp.vocab.vectors.n_keys,
                        "name": nlp.vocab.vectors.name,
                    }
                    meta.setdefault("name", "model%d" % i)
                    meta.setdefault("version", version)
                    meta["labels"] = nlp.meta["labels"]
                    meta_loc = output_path / ("model%d" % i) / "meta.json"
                    srsly.write_json(meta_loc, meta)
                    util.set_env_log(verbose)

                    _get_progress(
                        i,
                        losses,
                        scorer.scores,
                        output_stats,
                        beam_width=beam_width if has_beam_widths else None,
                        cpu_wps=cpu_wps,
                        gpu_wps=gpu_wps,
                    )
                    if i == 0 and "textcat" in pipeline:
                        textcats_per_cat = scorer.scores.get("textcats_per_cat", {})
                        for cat, cat_score in textcats_per_cat.items():
                            if cat_score.get("roc_auc_score", 0) < 0:
                                msg.warn(
                                    "Textcat ROC AUC score is undefined due to "
                                    "only one value in label '{}'.".format(cat)
                                )
                # Early stopping
                if n_early_stopping is not None:
                    current_score = _score_for_model(meta)
                    if current_score < best_score:
                        iter_since_best += 1
                    else:
                        iter_since_best = 0
                        best_score = current_score
                    if iter_since_best >= n_early_stopping:
                        iter_current = i + 1
                        num_iteration = max_iterations
                        break
    except Exception as e:
        msg.warn(
            "Aborting and saving the final best model. "
            "Encountered exception: {}".format(e),
            exits=1,
        )
    finally:
        best_pipes = nlp.pipe_names
        if disabled_pipes:
            disabled_pipes.restore()
            meta["pipeline"] = nlp.pipe_names
        with nlp.use_params(optimizer.averages):
            final_model_path = output_path / "model-final"
            nlp.to_disk(final_model_path)
            srsly.write_json(final_model_path / "meta.json", meta)

            meta_loc = output_path / "model-final" / "meta.json"
            final_meta = srsly.read_json(meta_loc)
            final_meta.setdefault("accuracy", {})
            final_meta["accuracy"].update(meta.get("accuracy", {}))
            final_meta.setdefault("speed", {})
            final_meta["speed"].setdefault("cpu", None)
            final_meta["speed"].setdefault("gpu", None)
            meta.setdefault("speed", {})
            meta["speed"].setdefault("cpu", None)
            meta["speed"].setdefault("gpu", None)
            # combine cpu and gpu speeds with the base model speeds
            if final_meta["speed"]["cpu"] and meta["speed"]["cpu"]:
                speed = _get_total_speed(
                    [final_meta["speed"]["cpu"], meta["speed"]["cpu"]]
                )
                final_meta["speed"]["cpu"] = speed
            if final_meta["speed"]["gpu"] and meta["speed"]["gpu"]:
                speed = _get_total_speed(
                    [final_meta["speed"]["gpu"], meta["speed"]["gpu"]]
                )
                final_meta["speed"]["gpu"] = speed
            # if there were no speeds to update, overwrite with meta
            if (
                    final_meta["speed"]["cpu"] is None
                    and final_meta["speed"]["gpu"] is None
            ):
                final_meta["speed"].update(meta["speed"])
            # note: beam speeds are not combined with the base model
            if has_beam_widths:
                final_meta.setdefault("beam_accuracy", {})
                final_meta["beam_accuracy"].update(meta.get("beam_accuracy", {}))
                final_meta.setdefault("beam_speed", {})
                final_meta["beam_speed"].update(meta.get("beam_speed", {}))
            srsly.write_json(meta_loc, final_meta)
        with msg.loading("Creating best model..."):
            _collate_best_model(final_meta, output_path, best_pipes)

def _score_for_model(meta):
    """ Returns mean score between tasks in pipeline that can be used for early stopping. """
    mean_acc = list()
    pipes = meta["pipeline"]
    acc = meta["accuracy"]
    if "tagger" in pipes:
        mean_acc.append(acc["tags_acc"])
    if "parser" in pipes:
        mean_acc.append((acc["uas"] + acc["las"]) / 2)
    if "ner" in pipes:
        mean_acc.append((acc["ents_p"] + acc["ents_r"] + acc["ents_f"]) / 3)
    if "textcat" in pipes:
        mean_acc.append(acc["textcat_score"])
    return sum(mean_acc) / len(mean_acc)

def _load_vectors(nlp, vectors):
    util.load_model(vectors, vocab=nlp.vocab)

def _load_pretrained_tok2vec(nlp, loc, base_components):
    """Load pretrained weights for the 'token-to-vector' part of the component
    models, which is typically a CNN. See 'spacy pretrain'. Experimental.
    """
    with loc.open("rb") as file_:
        weights_data = file_.read()
    loaded = []
    for name, component in nlp.pipeline:
        if hasattr(component, "model") and hasattr(component.model, "tok2vec"):
            if name in base_components:
                raise ValueError(Errors.E200.format(component=name))
            component.tok2vec.from_bytes(weights_data)
            loaded.append(name)
    return loaded

def _collate_best_model(meta, output_path, components):
    bests = {}
    meta.setdefault("accuracy", {})
    for component in components:
        bests[component] = _find_best(output_path, component)
    best_dest = output_path / "entities"
    shutil.copytree(path2str(output_path / "model-final"), path2str(best_dest))
    for component, best_component_src in bests.items():
        shutil.rmtree(path2str(best_dest / component))
        shutil.copytree(
            path2str(best_component_src / component), path2str(best_dest / component)
        )
        accs = srsly.read_json(best_component_src / "accuracy.json")
        for metric in _get_metrics(component):
            meta["accuracy"][metric] = accs[metric]
    srsly.write_json(best_dest / "meta.json", meta)

def _find_best(experiment_dir, component):
    accuracies = []
    for epoch_model in experiment_dir.iterdir():
        if epoch_model.is_dir() and epoch_model.parts[-1] != "model-final":
            accs = srsly.read_json(epoch_model / "accuracy.json")
            scores = [accs.get(metric, 0.0) for metric in _get_metrics(component)]
            # remove per_type dicts from score list for max() comparison
            scores = [score for score in scores if isinstance(score, float)]
            accuracies.append((scores, epoch_model))
    if accuracies:
        return max(accuracies)[1]
    else:
        return None

def _get_metrics(component):
    if component == "parser":
        return "las", "uas", "las_per_type", "token_acc"
    elif component == "tagger":
        return "tags_acc", "token_acc"
    elif component == "ner":
        return "ents_f", "ents_p", "ents_r", "ents_per_type", "token_acc"
    elif component == "textcat":
        return "textcat_score", "token_acc"
    return ("token_acc",)

def _configure_training_output(pipeline, use_gpu, has_beam_widths):
    row_head = ["Itn"]
    output_stats = []
    for pipe in pipeline:
        if pipe == "tagger":
            row_head.extend(["Tag Loss ", " Tag %  "])
            output_stats.extend(["tag_loss", "tags_acc"])
        elif pipe == "parser":
            row_head.extend(["Dep Loss ", " UAS  ", " LAS  "])
            output_stats.extend(["dep_loss", "uas", "las"])
        elif pipe == "ner":
            row_head.extend(["NER Loss ", "NER P ", "NER R ", "NER F "])
            output_stats.extend(["ner_loss", "ents_p", "ents_r", "ents_f"])
        elif pipe == "textcat":
            row_head.extend(["Textcat Loss", "Textcat"])
            output_stats.extend(["textcat_loss", "textcat_score"])
    row_head.extend(["Token %", "CPU WPS"])
    output_stats.extend(["token_acc", "cpu_wps"])

    if use_gpu >= 0:
        row_head.extend(["GPU WPS"])
        output_stats.extend(["gpu_wps"])

    if has_beam_widths:
        row_head.insert(1, "Beam W.")
    return row_head, output_stats

def _get_progress(
        itn, losses, dev_scores, output_stats, beam_width=None, cpu_wps=0.0, gpu_wps=0.0
):
    scores = {}
    for stat in output_stats:
        scores[stat] = 0.0
    scores["dep_loss"] = losses.get("parser", 0.0)
    scores["ner_loss"] = losses.get("ner", 0.0)
    scores["tag_loss"] = losses.get("tagger", 0.0)
    scores["textcat_loss"] = losses.get("textcat", 0.0)
    scores["cpu_wps"] = cpu_wps
    scores["gpu_wps"] = gpu_wps or 0.0
    scores.update(dev_scores)
    update_results(scores)
    formatted_scores = []
    for stat in output_stats:
        format_spec = "{:.3f}"
        if stat.endswith("_wps"):
            format_spec = "{:.0f}"
        formatted_scores.append(format_spec.format(scores[stat]))
    result = [itn + 1]
    result.extend(formatted_scores)
    if beam_width is not None:
        result.insert(1, beam_width)

def _get_total_speed(speeds):
    seconds_per_word = 0.0
    for words_per_second in speeds:
        if words_per_second is None:
            return None
        seconds_per_word += 1.0 / words_per_second
    return 1.0 / seconds_per_word

def create_results():
    with open('results_entities.csv', 'w', newline = '') as res:
        writer_object = csv.DictWriter(res, fieldnames=['loss','precision','recall','f1'])
        writer_object.writeheader()
        res.close()

def update_results(scores):
    with open('results_entities.csv', 'a', newline = '') as res:
        writer_object = csv.DictWriter(res, fieldnames=['loss','precision','recall','f1'])
        writer_object.writerow({'loss': scores['ner_loss'], 'precision': scores['ents_p'], 'recall': scores['ents_r'], 'f1': scores['ents_f']})
        res.close()

def get_num_iteration():
    global num_iteration
    return num_iteration

def get_num_progress():
    global max_iterations
    global num_iteration
    fraction_progress = (num_iteration / max_iterations) * 100
    num_progress = 0
    if ((fraction_progress - int(fraction_progress)) > 0.5):
        num_progress = int(fraction_progress) + 1
    else:
        num_progress = int(fraction_progress)
    return num_progress